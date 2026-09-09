# -*- coding: utf-8 -*-
"""N-94 — Die SPANNE gegen den Nullpunkt statt „monoton ja/nein"

## Der Anlass

B10 hat gezeigt: `schnitt` erfüllt die Monotonie-Vorgabe **genauso wenig
wie `funding`** - und `funding` läuft live. Beide haben auf `frei`
denselben Knick (Fünftel 1 über Fünftel 0).

> Die Monotonie-Vorgabe war als Schutz vor Überanpassung gedacht, ist
> aber nie an den LAUFENDEN Beiträgen geprüft worden - und `funding`
> bricht sie seit dem 30.08.

⚠️ Sie streng anzuwenden hieße, den Bestand mitzureißen. Sie fallen zu
lassen braucht einen **Ersatz**, der Überanpassung sonst abfängt.

## Der Vorschlag, und warum er besser ist

**Die SPANNE der Stufen gegen die des NULLPUNKTS** statt „monoton
ja/nein":

    schnitt  frei   Spanne 3,55
    funding  frei   Spanne 3,15
    zufall   frei   Spanne 0,28

⚠️⚠️ **Aber 0,28 ist EINE Ziehung.** Eine einzelne Zahl ist kein
Nullpunkt - dieselbe Regel wie überall sonst. Deshalb wird hier die
VERTEILUNG der Nullspannen gemessen: 40 Ziehungen mit gemischten Rängen,
genau wie in `pruefe_auswahl`.

**Warum die Spanne besser ist als Monotonie:**

| | Monotonie | Spanne gegen den Nullpunkt |
|---|---|---|
| Aussage | ja/nein, ohne Maß | eine Zahl mit Nullverteilung |
| Rauschen | fünf verrauschte Punkte sind selten exakt monoton | die Spanne mittelt nicht weg, sie summiert |
| Fehlalarm | unbekannt | messbar |
| Bestand | `funding` bricht sie | wird hier mitgemessen |

## Was gemessen wird

    1  Die Stufenspanne je Kandidat auf `frei` (Live-Ableitung, Median)
    2  Die VERTEILUNG der Nullspannen - 40 Ziehungen mit gemischten
       Rängen, dieselbe Konstruktion wie die Nullkontrolle der Norm
    3  Wo liegt die beobachtete Spanne in dieser Verteilung?

    Kriterium (vorab): Spanne > 97,5. Perzentil der Nullspannen
                       -> Fehlalarmquote 2,5 %, wie der Messstandard

⚠️ Die Kontrolle `zufall` MUSS durchfallen. Tut sie es nicht, taugt das
Kriterium nicht - dann ist die Spanne selbst schon Rauschen.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    funding, schnitt   bestehen deutlich (3,15 und 3,55 gegen ~0,3)
    zufall             fällt durch
    turnover, oi       bestehen, aber knapper (schmalere Abdeckung)
    rsi, amihud        fallen durch - sie tragen auch sonst nicht

⚠️ Besteht `zufall`, ist das Kriterium wertlos und die Monotonie bleibt
die einzige Hürde - dann müsste über `funding` neu entschieden werden.

    python n94_spanne_statt_monotonie.py
"""
from __future__ import annotations

import statistics as st
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402

CRV = 2.0
NULL_ZIEH = 40
SAAT = 20260909
KANDIDATEN = ("schnitt", "funding", "turnover", "oi_aenderung", "vola",
              "schnitt50", "rsi", "amihud", "zufall")


def stufen_frei(je_tag, mische=None):
    """Die Live-Ableitung auf `frei` - Median je Fuenftel, ohne Auswahl."""
    sammel = {k: [] for k in range(5)}
    for zeilen in je_tag.values():
        if len(zeilen) < 15:
            continue
        w = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        if mische is not None:
            # ⚠️ DIESELBE Nullkonstruktion wie in `pruefe_auswahl`: die
            # RAENGE werden gemischt, die Ergebnisse bleiben stehen.
            r = mische.permutation(r)
        for k in range(5):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(not sammel[k] for k in range(5)):
        return None
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    f = 1.0 / (1.0 + CRV)
    return [100.0 * (werte[k] - mittel) * f / 2.0 for k in range(5)]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    zus = zusatzquellen()

    print("=" * 104)
    print("N-94 — die SPANNE gegen den Nullpunkt statt 'monoton ja/nein'")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  Menge `frei` · Live-Ableitung · %d Nullziehungen "
          "(gemischte Raenge)" % NULL_ZIEH)
    print("  Kriterium VORAB: Spanne > 97,5. Perzentil der Nullspannen "
          "-> 2,5 %% Fehlalarm")
    print()
    print("  %-14s %8s %9s %9s %9s %8s  %s"
          % ("Kandidat", "Spanne", "Null Med", "Null p97,5", "Null max",
             "x Null", "Urteil"))

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:56]))
            continue
        p = stufen_frei(je)
        if p is None:
            print("  %-14s -> nicht messbar" % kand)
            continue
        spanne = max(p) - min(p)
        nulls = []
        for z in range(NULL_ZIEH):
            q = stufen_frei(je, mische=np.random.default_rng(SAAT + z))
            if q:
                nulls.append(max(q) - min(q))
        if len(nulls) < NULL_ZIEH // 2:
            print("  %-14s %8.2f  Nullverteilung nicht messbar"
                  % (kand, spanne))
            continue
        med = float(np.median(nulls))
        p975 = float(np.percentile(nulls, 97.5))
        mx = float(max(nulls))
        besteht = spanne > p975
        erg[kand] = (spanne, med, p975, mx, besteht, p)
        print("  %-14s %8.2f %9.2f %9.2f %9.2f %8.1f  %s"
              % (kand, spanne, med, p975, mx,
                 spanne / med if med > 0 else float("nan"),
                 "✔ BESTEHT" if besteht else "traegt nicht"), flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 104)
    print("TAUGT DAS KRITERIUM?")
    print("=" * 104)
    zf = erg.get("zufall")
    if zf is None:
        print("  ⚠️⚠️ Die Kontrolle war nicht messbar - der Lauf gilt "
              "nicht.")
        return 1
    if zf[4]:
        print("  ⚠️⚠️⚠️ DIE KONTROLLE BESTEHT (%.2f gegen p97,5 %.2f) - "
              "das Kriterium taugt NICHT." % (zf[0], zf[2]))
        print("     Dann ist die Spanne selbst schon Rauschen, und die "
              "Monotonie bleibt die einzige Huerde -")
        print("     mit der Folge, dass ueber `funding` neu zu "
              "entscheiden waere.")
        return 1
    print("  ✔ Die Kontrolle `zufall` faellt durch: Spanne %.2f gegen "
          "p97,5 %.2f." % (zf[0], zf[2]))
    print()
    best = [k for k, v in erg.items() if v[4] and k != "zufall"]
    durch = [k for k, v in erg.items() if not v[4] and k != "zufall"]
    print("  BESTEHEN:      %s" % (", ".join(best) or "keiner"))
    print("  fallen durch:  %s" % (", ".join(durch) or "keiner"))
    print()
    print("  ⚠️ Und die Gegenprobe zur MONOTONIE - wer waere wie "
          "beurteilt worden?")
    print("     %-14s %-14s %s" % ("Kandidat", "Spannenurteil",
                                   "Monotonie"))
    for kand, v in erg.items():
        p = v[5]
        mono = (all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
                or all(p[i] <= p[i + 1] + 1e-9 for i in range(4)))
        print("     %-14s %-14s %s"
              % (kand, "✔ besteht" if v[4] else "faellt durch",
                 "✔ monoton" if mono else "⚠️ nicht monoton"))
    print()
    print("  ⚠️⚠️ Wo die beiden Spalten auseinandergehen, entscheidet die "
          "Wahl des Kriteriums.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
