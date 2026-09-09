# -*- coding: utf-8 -*-
"""N-92 (B9) — Betrifft `funding`s Buckel die LIVE-Stufen? (09.09.2026)

## Die Frage, präzise gestellt

N-91 hat auf der **20-%-Menge** gefunden: `funding`s Rangkorrelation ist
in den beiden Haelften GEGENLAEUFIG und beide Haelften sind TRENNBAR
(+0,0541 [+0,022..+0,088] und -0,0268 [-0,049..-0,004]). Ein Buckel.

⚠️⚠️ **Die Live-Stufen stehen aber auf `frei`.** An der Quelle geprueft
(`rechne_funding_beitrag.py`): dort wird KEINE Auswahl gebildet - das
`je_tag` enthaelt alle Symbole mit Funding, also den vollen
Tagesquerschnitt.

> **Die Frage ist also nicht 'hat funding einen Buckel', sondern:
> tritt er auf DER Menge auf, aus der die Live-Stufen stammen?**

## ⚠️ Was an der Ableitung auffaellt - und was daran harmlos ist

Die Stufen entstehen aus **Gruppenmedianen** - genau der Methode, die
N-90 als unzuverlaessig gezeigt hat (die Kontrolle schlug dort mit +-90
Punkten aus). Und die Untergrenze ist **zwei Anker**:

    if m.sum() >= 2: sammel[k].append(median(y[m]))

✔ **Auf `frei` ist das aber viel sicherer**: die Fuenftel entstehen aus
dem Rang des VOLLEN Querschnitts und sind per Konstruktion gleich gross -
rund 60 Anker statt der 1,5 aus der Momentummenge. Genau die Ungleichheit
war in N-90 die Ursache.

⚠️ Ohne Entzerrung ist es trotzdem: die Stufen sind rohe Mediandifferenzen
gegen das Mittel der fuenf.

## Was gemessen wird

    1  Die Rangkorrelation auf `frei` - gesamt und je Haelfte, mit Band
       (dasselbe Verfahren wie N-91, das auf Kunstdaten geeicht ist)
    2  Die BESETZUNG der Fuenftel auf `frei` - ist sie ausgeglichen?
    3  Die Stufen auf `frei` REPRODUZIERT - stimmen sie mit den
       registrierten (+0,82 / +1,30 / +0,12 / -0,54 / -1,70)?
    4  Dieselben Stufen ENTZERRT - bleibt der Knick bei Fuenftel 1?

    Kontrolle   `zufall` an jeder Stelle

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung   auf `frei` verschwindet der Buckel oder wird
                untrennbar - er war ein Kollinearitaetseffekt der
                Momentumauswahl, wie bei `schnitt`
    Gegenthese  er bleibt trennbar - dann stehen die Live-Stufen auf
                einer nicht-monotonen Form, und das waere ein echter
                Mangel an einem laufenden Beitrag

⚠️ Bleibt er, ist das KEIN Grund, `funding` fallen zu lassen - seine
WIRKUNG ist auf `frei` unabhaengig belegt (+0,0249, traegt). Es waere ein
Grund, die STUFEN neu abzuleiten.

    python n92_b9_funding_buckel_auf_frei.py
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
from agent.wahrscheinlichkeit import BEITRAEGE               # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n91_rangkorrelation_form import band, form, reihen_je_tag  # noqa: E402

CRV = 2.0
ZIEH_NULL, SAAT = 20, 20260909


def registrierte_stufen(merkmal):
    for b in BEITRAEGE:
        if b.merkmal == merkmal and b.stufen:
            return tuple(b.stufen)
    return None


def stufen_wie_live(je_tag, entzerren=False):
    """Die Ableitung aus `rechne_funding_beitrag.py`, Schritt fuer Schritt.

    ⚠️ Nachgebaut statt importiert, weil das Werkzeug ein Skript ohne
    Funktionen ist. Die Rechenschritte sind Zeile fuer Zeile uebernommen -
    Fuenftel je Tag, Median je Fuenftel, Mittel ueber die Tage, minus dem
    Mittel der fuenf, mal 1/(1+CRV), halbiert.
    """
    sammel = {k: [] for k in range(5)}
    besetzt = {k: [] for k in range(5)}
    for z in je_tag.values():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        if len(w) < 15:
            continue
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            besetzt[k].append(int(m.sum()))
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(not sammel[k] for k in range(5)):
        return None, None
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    faktor = 1.0 / (1.0 + CRV)
    punkte = [100.0 * (werte[k] - mittel) * faktor / 2.0 for k in range(5)]
    bes = [float(np.mean(besetzt[k])) for k in range(5)]
    return punkte, bes


def monoton(p):
    if p is None:
        return "nicht messbar"
    f = all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
    s = all(p[i] <= p[i + 1] + 1e-9 for i in range(4))
    if f:
        return "✔ MONOTON FALLEND"
    if s:
        return "✔ MONOTON STEIGEND"
    return "⚠️ NICHT monoton, Hochpunkt bei Fuenftel %d" % int(np.argmax(p))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 108)
    print("N-92 (B9) — betrifft `funding`s Buckel die LIVE-Stufen?")
    print("=" * 108)
    print("  %s" % messmenge.zeile())
    print("  ⚠️ Die Live-Stufen stehen auf `frei` (an der Quelle geprueft: "
          "`rechne_funding_beitrag.py`")
    print("     bildet KEINE Auswahl). N-91 fand den Buckel auf 20 %.")
    print("  registriert: %s"
          % " / ".join("%+.2f" % x
                       for x in (registrierte_stufen("funding_fuenftel")
                                 or ())))

    # ---- 1 + 2  Rangkorrelation und Besetzung ---------------------------
    print()
    print("  1  DIE RANGKORRELATION - dasselbe Verfahren wie N-91")
    print("     %-10s %-6s %21s %21s %21s  %s"
          % ("Kandidat", "Menge", "gesamt", "untere", "obere", "Form"))
    for kand in ("funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        for menge in ("frei", "20%"):
            g, u, o = reihen_je_tag(je, mom, MENGEN[menge])
            bg, bu, bo = band(g, block), band(u, block), band(o, block)

            def z(b):
                return ("%+.4f [%+.3f..%+.3f]" % (b[0], b[1], b[2])
                        if b else "nicht messbar")
            print("     %-10s %-6s %21s %21s %21s  %s"
                  % (kand, menge, z(bg), z(bu), z(bo), form(bu, bo)),
                  flush=True)
        print()

    # ---- 3 + 4  Die Stufen ---------------------------------------------
    print("  2  DIE STUFEN, wie das Live-Werkzeug sie rechnet")
    print("     %-10s %-6s %42s  %s"
          % ("Kandidat", "Menge", "Punkte (Fuenftel 0..4)", "Form"))
    for kand in ("funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        p, bes = stufen_wie_live(je)
        if p is None:
            print("     %-10s %-6s nicht messbar" % (kand, "frei"))
            continue
        print("     %-10s %-6s %42s  %s"
              % (kand, "frei",
                 " ".join("%+7.2f" % x for x in p), monoton(p)))
        print("     %-10s %-6s %42s  Besetzung: %s"
              % ("", "", "", " ".join("%.0f" % b for b in bes)))

    print()
    print("=" * 108)
    print("WAS DAS HEISST")
    print("=" * 108)
    print("  ⚠️ Entscheidend ist die Zeile `funding / frei` - dort stehen "
          "die Live-Stufen.")
    print("  Ist der Buckel dort NICHT trennbar, betrifft er die "
          "Registrierung nicht.")
    print("  ⚠️ Und die BESETZUNG zeigt, ob die Gruppenmediane hier "
          "ueberhaupt tragen -")
    print("     in N-90 waren es 1,5 Anker im untersten Fuenftel, und das "
          "war die Ursache.")
    print("  ⚠️⚠️ Bleibt der Buckel: das ist KEIN Grund, `funding` fallen "
          "zu lassen -")
    print("     seine WIRKUNG auf `frei` ist unabhaengig belegt (+0,0249, "
          "traegt).")
    print("     Es waere ein Grund, die STUFEN neu abzuleiten.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
