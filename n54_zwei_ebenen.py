# -*- coding: utf-8 -*-
"""N-54 — SIND ES ZWEI EBENEN? `vola` entscheidet OB, funding/turnover WOHIN (06.09.)

## Woher die Frage kommt

N-53 hat die drei Groessen erstmals durch dasselbe richtungsreine Verfahren
geschickt:

    Groesse    G0 (regist.)  GS (Richtung)  AUF (Kanal)
    funding      +0,00257      +0,00197 ✔     +0,00143  (1/5, ns)
    turnover     +0,00168 ns   +0,00512 ✔     -0,00218  (ns)
    vola         +0,01350 ✔    -0,00041 ✖     +0,03088 ✔

**Die drei liegen sauber getrennt:** `funding` und `turnover` tragen
RICHTUNG und reiten den Aufloesungskanal NICHT. `vola` ist genau umgekehrt.

Daraus faellt eine Bauform, die nicht erfunden, sondern abgelesen ist:

    `vola`     sorgt dafuer, dass ein Anker in der Frist ueberhaupt
               ENTSCHIEDEN wird (Aufloesungsquote +3,1 Punkte)
    funding    sagen dann, nach welcher SEITE
    turnover

## ⚠️ Die pruefbare Vorhersage — und sie kann scheitern

Wenn das stimmt, muessen `funding` und `turnover` **im guten vola-Drittel
staerker wirken** als im schlechten. Denn dort wird ueberhaupt entschieden,
und nur eine Entscheidung kann eine Richtung haben.

    Trifft das zu   -> zwei Ebenen, die zusammenspielen. `vola` gehoert
                       NICHT als Summand in `BEITRAEGE`, sondern als
                       BEDINGUNG davor (Geometrie/Horizont).
    Trifft es nicht -> die Ebenen sind unabhaengig. Dann ist `vola` nur
                       ein Geometriehebel ohne Bezug zur Bewertung, und
                       die Bauform bleibt so, wie sie ist.

⚠️ Beides ist ein brauchbares Ergebnis. Das hier ist keine Suche nach
   Bestaetigung - die Gegenrichtung ist vorab benannt.

## ⚠️⚠️ Was die Messung NICHT darf

Sie darf nicht einfach im besten Drittel eine groessere Zahl finden und
daraus schliessen. Zwei Fallen sind vorab benannt:

  1  MENGE. Ein Drittel hat ein Drittel der Anker. Kleinere Mengen
     streuen staerker - das allein macht Unterschiede.
     -> Gegenmassnahme: das BAND je Drittel, und die Frage ist, ob sich
        die Baender ueberlappen. Kein Punktvergleich.
  2  DER KANAL SELBST. Im guten vola-Drittel loest MEHR auf. Eine hoehere
     G0-Wirkung koennte allein daher kommen.
     -> Gegenmassnahme: die Vorhersage wird an GS geprueft, nicht an G0.
        GS ist auf Aufloesung bedingt - der Mengeneffekt ist heraus.

    python n54_zwei_ebenen.py --probe
    python n54_zwei_ebenen.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
from n52_vola_geometrieprobe import (band, kontrolle,        # noqa: E402
                                     traegt, _ausgang, MISCHUNGEN)

CRV, BRUCH, HORIZONT = 2.0, 5.0, 5
VORLAUF = 260
DRITTEL = ("vola-Drittel 0 (ruhig, loest oft auf)",
           "vola-Drittel 1 (mittel)",
           "vola-Drittel 2 (lebhaft, loest selten auf)")


def baue(reihen, zusatz):
    """je Tag: Anker mit BEIDEN Kennzahlen - der externen und `vola`."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        for i in range(max(B.SCHWANKUNG, VORLAUF), len(c) - HORIZONT):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            w = je_sym.get(tage[i])
            if w is None:
                continue
            med = float(np.median(br[i - 250:i + 1]))
            if not np.isfinite(med) or med <= 0:
                continue
            roh = _ausgang(c, h, t, i, float(br[i]), CRV)
            symm = _ausgang(c, h, t, i, float(br[i]), 1.0)
            je_tag.setdefault(tage[i], []).append({
                "kennzahl": float(w),
                "vola": float(br[i] / med),
                "g0": 1.0 if roh > 0 else 0.0,
                "auf": 0.0 if roh == 0 else 1.0,
                "gs": (1.0 if symm > 0 else 0.0) if symm != 0 else None})
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def regel_im_drittel(je_tag, feld, welches, mische=None):
    """Die Regelwirkung der EXTERNEN Kennzahl INNERHALB eines vola-Drittels.

    ⚠️ Das vola-Drittel wird ueber ALLE Anker des Tages gebildet, dann
    wird darin nach der externen Kennzahl gerangt. Wer zuerst filtert und
    dann drittelt, bekommt je Groesse eine andere Drittelgrenze.
    """
    aus = {}
    for tag, z0 in je_tag.items():
        v = np.array([x["vola"] for x in z0], float)
        f = np.minimum((W.rang(v) * 3).astype(int), 2)
        z = [x for j, x in enumerate(z0)
             if f[j] == welches and x[feld] is not None]
        if len(z) < 9:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        g = np.minimum((r * 3).astype(int), 2)
        frei = g < 2
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        aus[tag] = float(y[frei].mean()) - float(y.mean())
    return aus


def kontrolle_im_drittel(je_tag, feld, welches, echt):
    tr = 0
    for k in range(MISCHUNGEN):
        rng = np.random.default_rng(81000 + k)
        b = band(regel_im_drittel(je_tag, feld, welches, mische=rng))
        if b and abs(b[0]) >= abs(echt):
            tr += 1
    return tr


def zeige(je_tag, name):
    print()
    print("  %s  (%d Tage, %d Anker)"
          % (name.upper(), len(je_tag), sum(len(z) for z in je_tag.values())))
    erg = {}
    for feld, lab in (("gs", "GS  (Richtung, entscheidet)"),
                      ("g0", "G0  (Barrieren-Quote)"),
                      ("auf", "AUF (Aufloesungsquote)")):
        print("     %s" % lab)
        werte = []
        for d in range(3):
            b = band(regel_im_drittel(je_tag, feld, d))
            if not b:
                print("       %-38s zu wenige Tage" % DRITTEL[d])
                werte.append(None)
                continue
            k = kontrolle_im_drittel(je_tag, feld, d, b[0])
            tr = traegt(b, k)
            print("       %-38s %+9.5f [%+.5f .. %+.5f]  %d/%d %s"
                  % (DRITTEL[d], b[0], b[1], b[2], k, MISCHUNGEN,
                     "✔" if tr else ""), flush=True)
            werte.append(b)
        erg[feld] = werte
    return erg


def urteile(name, erg):
    """⚠️ Kein Punktvergleich - die BAENDER muessen sich trennen."""
    g = erg.get("gs") or [None, None, None]
    if not (g[0] and g[2]):
        print("     %-10s zu wenige Daten fuer das Urteil" % name)
        return
    getrennt = g[0][1] > g[2][2]        # unteres Band 0 ueber oberem Band 2
    print("     %-10s GS gut %+.5f [%+.5f .. %+.5f] · schlecht %+.5f "
          "[%+.5f .. %+.5f]"
          % (name, g[0][0], g[0][1], g[0][2], g[2][0], g[2][1], g[2][2]))
    if getrennt:
        print("                ✔ DIE BAENDER TRENNEN SICH - `%s` wirkt im "
              "guten vola-Drittel" % name)
        print("                  nachweisbar staerker. Zwei Ebenen, die "
              "zusammenspielen.")
    else:
        print("                ⚠️ die Baender ueberlappen - kein Beleg fuer "
              "ein Zusammenspiel.")
        print("                  Die Ebenen sind dann UNABHAENGIG, und `%s` "
              "wirkt ueberall gleich." % name)


def main() -> int:
    t0 = time.time()
    print("=" * 92)
    print("N-54 — zwei Ebenen? `vola` entscheidet OB, funding/turnover WOHIN")
    print("=" * 92)
    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = (("funding", F.lade_funding()),
               ("turnover", MB.reihe("data/onchain_historie.db", "splycur")))
    alle = {}
    for name, q in quellen:
        alle[name] = zeige(baue(reihen, q), name)

    print()
    print("=" * 92)
    print("DAS URTEIL — trennen sich die Baender zwischen gutem und "
          "schlechtem Drittel?")
    print("=" * 92)
    for name in ("funding", "turnover"):
        urteile(name, alle[name])
    print()
    print("  ⚠️ Geprueft wird an GS, nicht an G0: im guten vola-Drittel")
    print("     loest mehr auf, und eine hoehere G0-Wirkung koennte allein")
    print("     daher kommen. GS ist auf Aufloesung bedingt.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
