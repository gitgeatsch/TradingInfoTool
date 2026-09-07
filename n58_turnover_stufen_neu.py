# -*- coding: utf-8 -*-
"""N-58 — `turnover`s STUFEN NEU HERGELEITET (07.09.2026)

## Warum überhaupt neu

N-56 (2.139): die registrierte Tabelle **reproduziert nicht**.

    registriert   +0,0616 R
    gemessen      -0,06293 R  [-0,13183 .. -0,00785]   Vorzeichen gedreht

Und die Fünftel haben keine Ordnung: +0,009 · +0,053 · **-0,265** ·
-0,041 · **+0,229**. Das BESTE ist Fuenftel 4 - das die Live-Tabelle mit
**-2,40** am haertesten bestraft. Es sind die groessten Stufen im System.

⚠️ Die GROESSE bleibt: `turnover` traegt Richtung (N-53, GS +0,00512, der
staerkste der drei). Neu herzuleiten ist allein die TABELLE.

## ⚠️⚠️ DREI ENTSCHEIDUNGEN, die vorab feststehen und begruendet sind

**1 - Die ZIELGROESSE: Treffer unter den AUFGELOESTEN.**
N-57 (2.140) hat gemessen, dass bei H5 31,4 % der Anker flach auslaufen -
und die Kalibrierung sie wie Stops zaehlt, obwohl die Produktion **keinen
Zeitausstieg** kennt. Unter den Aufgeloesten liegt die Trefferquote bei
34,8 %, und die Formel setzt `basisrate(2,0) = 33,3 %`. **Die Formel
stimmt fuer die Produktion; die alte Messkonvention nicht.**

**2 - Die GEOMETRIE: die echte.**
`max(5 % Kurs, 0,75 x ATR)`, Deckel 25 %, CRV 2,0 - der Rauschboden aus
`entscheidungsrechnung._boeden`. Nicht die Messkonvention 1,0 x ATR.

**3 - Der HORIZONT: H20.**
Nicht H5 (dort laufen 31,4 % flach aus statt 5,3 %), und nicht
"bis zur Aufloesung" - dafuer verlangte `messnorm._block` einen Block von
360 Tagen, und 2.500 Tage ergaeben nur 7 Bloecke statt der geforderten 20.
Bei H20 ist der Block 60 und es sind rund 40 Bloecke. ⚠️ Die Blocklaenge
wird trotzdem NACHGEPRUEFT (`pruefe_block`), nicht angenommen.

## Die FORM — und warum sie nicht 50/50 sein kann

2.133: belegt ist eine **Zweiteilung**, keine Fuenfteilung. Aber das
Merkmal heisst `turnover_fuenftel` und liefert 0..4 - **ein 50/50-Schnitt
liegt zwischen Fuenftel 2 und 3 und ist auf dieser Skala nicht
darstellbar.** Gemessen werden deshalb genau die beiden Schnitte, die
BAUBAR sind:

    Schnitt A   Fuenftel 0,1   gegen   2,3,4      (40/60)
    Schnitt B   Fuenftel 0,1,2 gegen   3,4        (60/40)

**Gemessen wird die Form, die gebaut wird** - nicht eine, die sich
nachher nicht umsetzen laesst.

## Gegenprüfungen — alle vorab benannt

    A  Die fuenf Fuenftel EINZELN. Gibt es doch eine Ordnung?
    B  BEIDE Historienhaelften. Was ueber die Zeit nicht haelt, gilt nicht.
    C  H5 daneben - wie stark haengt das Ergebnis am Horizont?
    D  Die ALTE Zielgroesse (rohe Quote, flach = Verlust) zum Vergleich -
       wieviel macht die Umstellung aus?
    E  Zufallskontrolle mit FUENF Mischungen.
    F  Trennschaerfe: welcher gepflanzte Effekt wird noch gefunden?

    python n58_turnover_stufen_neu.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                          # noqa: E402
from agent import entscheidungsrechnung as E                 # noqa: E402
from agent.krypto.backward_tracking import (                 # noqa: E402
    PSEUDO_STICHPROBE, schrumpfe_zu_neutral)

BRUCH = 5.0
CRV = float(E.GRENZEN["crv"])
K_ATR = float(E.GRENZEN["stop_min_atr"])
MIN_REL = float(E.GRENZEN["stop_min_relativ"])
MAX_REL = float(E.GRENZEN["stop_max_relativ"])
MISCHUNGEN = 5
MIN_JE_TAG = 15
SCHNITTE = (("A  0,1 | 2,3,4  (40/60)", 2), ("B  0,1,2 | 3,4  (60/40)", 3))


def fenster(x, breite):
    from numpy.lib.stride_tricks import sliding_window_view
    return sliding_window_view(x[1:], breite)


def baue(reihen, zusatz, hz):
    """je Tag: Anker mit turnover-Kennzahl und dem Ausgang in ECHTER Geometrie."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        n = len(c)
        if n < hz + B.SCHWANKUNG + 5:
            continue
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        if not je_sym:
            continue
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        kaputt = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        bruch_f = fenster(np.concatenate([[False], kaputt]), hz).any(axis=1)
        hoch_f, tief_f = fenster(h, hz), fenster(t, hz)
        gueltig = min(len(hoch_f), n - hz)
        idx = np.arange(B.SCHWANKUNG, gueltig)
        idx = idx[np.isfinite(br[idx]) & (br[idx] > 0) & ~bruch_f[idx]]
        if not len(idx):
            continue
        # ⚠️ DIE ECHTE GEOMETRIE, nicht 1,0 x ATR
        weite = np.minimum(np.maximum(MIN_REL * c[idx], K_ATR * br[idx]),
                           MAX_REL * c[idx])
        ziel, stop = c[idx] + CRV * weite, c[idx] - weite
        tr_z = hoch_f[idx] >= ziel[:, None]
        tr_s = tief_f[idx] <= stop[:, None]
        tz = np.where(tr_z.any(axis=1), tr_z.argmax(axis=1) + 1, 0)
        ts = np.where(tr_s.any(axis=1), tr_s.argmax(axis=1) + 1, 0)
        # ⚠️ GLEICHSTAND AN DEN STOP (N-55)
        verlust = (ts > 0) & ((tz == 0) | (ts <= tz))
        gewinn = (tz > 0) & ~verlust
        for j, i in enumerate(idx):
            w = je_sym.get(tage[i])
            if w is None:
                continue
            aufgeloest = bool(gewinn[j] or verlust[j])
            je_tag.setdefault(tage[i], []).append({
                "kennzahl": float(w),
                # DIE NEUE Zielgroesse: nur Aufgeloeste, None = faellt weg
                "q_auf": (1.0 if gewinn[j] else 0.0) if aufgeloest else None,
                # DIE ALTE zum Vergleich: flach zaehlt als Nicht-Treffer
                "q_roh": 1.0 if gewinn[j] else 0.0})
    return {t: z for t, z in je_tag.items() if len(z) >= MIN_JE_TAG}


def faecher(je_tag, feld, k, mische=None, pflanze=0.0):
    """Je Fach die Tagesreihe der Abweichung vom Tagesmittel (in PUNKTEN)."""
    reihen = [dict() for _ in range(k)]
    for tag, z0 in je_tag.items():
        z = [x for x in z0 if x[feld] is not None]
        if len(z) < max(MIN_JE_TAG, k * 3):
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * k).astype(int), k - 1)
        if pflanze:
            # ⚠️ Trennschaerfe: einen Effekt der Groesse `pflanze` PUNKTE
            # in das unterste Fach legen und sehen, ob er gefunden wird.
            y = y + (f == 0) * (pflanze / 100.0)
        basis = float(y.mean())
        for i in range(k):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = 100.0 * (float(y[m].mean()) - basis)
    return reihen


def gruppen(je_tag, feld, schnitt, mische=None, pflanze=0.0):
    """Zwei Gruppen auf der FUENFTEL-Skala, geteilt vor Fuenftel `schnitt`."""
    unten, oben = dict(), dict()
    for tag, z0 in je_tag.items():
        z = [x for x in z0 if x[feld] is not None]
        if len(z) < MIN_JE_TAG:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * 5).astype(int), 4)
        if pflanze:
            y = y + (f < schnitt) * (pflanze / 100.0)
        m = f < schnitt
        if m.sum() < 3 or (~m).sum() < 3:
            continue
        basis = float(y.mean())
        unten[tag] = 100.0 * (float(y[m].mean()) - basis)
        oben[tag] = 100.0 * (float(y[~m].mean()) - basis)
    return unten, oben


def band(d, block, zieh=2000, saat=20260907):
    rng = np.random.default_rng(saat)
    x = np.array([d[q] for q in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    a = np.empty(zieh)
    for j in range(zieh):
        s = rng.choice(st, nb)
        a[j] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(a, 2.5)),
            float(np.percentile(a, 97.5)))


def traegt(b, k):
    return b is not None and (b[1] > 0 or b[2] < 0) and k == 0


def kontrolle(bauer, echt, block):
    tr = 0
    for i in range(MISCHUNGEN):
        rng = np.random.default_rng(58000 + i)
        d = bauer(rng)
        b = band(d, block)
        if b and abs(b[0]) >= abs(echt):
            tr += 1
    return tr


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-58 — `turnover`s Stufen neu hergeleitet")
    print("=" * 100)
    print("  Zielgroesse: Treffer unter den AUFGELOESTEN (2.140)")
    print("  Geometrie:   max(%.0f %% Kurs, %.2f x ATR), Deckel %.0f %%, "
          "CRV %.1f" % (100 * MIN_REL, K_ATR, 100 * MAX_REL, CRV))
    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    quelle = MB.reihe("data/onchain_historie.db", "splycur")

    for hz in (20, 5):
        block = N._block(hz)
        je = baue(reihen, quelle, hz)
        auf = sum(1 for z in je.values() for x in z if x["q_auf"] is not None)
        ges = sum(len(z) for z in je.values())
        print()
        print("#" * 100)
        print("# HORIZONT %d   ·   Block %d   ·   %d Tage, %d Anker "
              "(%d aufgeloest = %.1f %%)"
              % (hz, block, len(je), ges, auf, 100 * auf / max(1, ges)))
        print("#" * 100)

        # --- Blocklaenge BELEGEN, nicht annehmen -----------------------
        probe = gruppen(je, "q_auf", 2)[0]
        bp = N.pruefe_block(probe, block)
        print("  Blockpruefung: Autokorrelation bei Abstand %d = %+.3f -> %s"
              % (bp["lag"], bp["ak"], bp["grund"]))
        if not bp["ok"]:
            print("  ⚠️ Der Block ist zu kurz - das Band waere zu eng.")

        # --- A: die fuenf Fuenftel einzeln -----------------------------
        print()
        print("  A  DIE FUENF FUENFTEL EINZELN (Punkte auf die Quote)")
        print("     %-10s %10s %24s  %s"
              % ("Fuenftel", "Punkte", "Band", "Kontrolle"))
        for feld, lab in (("q_auf", "neu"), ("q_roh", "alt")):
            werte = []
            for i, d in enumerate(faecher(je, feld, 5)):
                b = band(d, block)
                werte.append(b[0] if b else float("nan"))
                if feld != "q_auf":
                    continue
                k = kontrolle(lambda r, i=i: faecher(je, feld, 5, mische=r)[i],
                              b[0] if b else 0.0, block)
                print("     %-10d %+10.3f [%+.3f .. %+.3f]  %d/%d %s"
                      % (i, b[0], b[1], b[2], k, MISCHUNGEN,
                         "✔" if traegt(b, k) else ""), flush=True)
            print("     %-10s %s" % ("(%s)" % lab, "  ".join(
                "%+.3f" % x for x in werte)))

        # --- B/C: die beiden BAUBAREN Schnitte -------------------------
        print()
        print("  B  DIE ZWEITEILUNG — nur die BAUBAREN Schnitte")
        beste = None
        for lab, sch in SCHNITTE:
            u, o = gruppen(je, "q_auf", sch)
            bu, bo = band(u, block), band(o, block)
            if not bu or not bo:
                print("     %-26s zu wenige Tage" % lab)
                continue
            ku = kontrolle(lambda r, s=sch: gruppen(je, "q_auf", s,
                                                    mische=r)[0],
                           bu[0], block)
            tr = traegt(bu, ku)
            print("     %-26s unten %+7.3f [%+.3f .. %+.3f]  %d/%d %s"
                  % (lab, bu[0], bu[1], bu[2], ku, MISCHUNGEN,
                     "✔ TRAEGT" if tr else ""))
            print("     %-26s oben  %+7.3f [%+.3f .. %+.3f]"
                  % ("", bo[0], bo[1], bo[2]))
            if tr and (beste is None or abs(bu[0]) > abs(beste[1][0])):
                beste = (lab, bu, bo, sch, ku, len(u))
            # ⚠️ SCHRUMPFUNG nach der dokumentierten Regel, nicht "÷2"
            for nam, b, d in (("unten", bu, u), ("oben", bo, o)):
                s = schrumpfe_zu_neutral(b[0], len(d), 0.0, PSEUDO_STICHPROBE)
                print("     %-26s %s roh %+.3f -> geschrumpft %+.3f "
                      "(Gewicht %.3f, n=%d, k=%d)"
                      % ("", nam, s["roh"], s["gewichtet"], s["gewicht"],
                         s["n"], s["k"]))

        # --- F: Trennschaerfe ------------------------------------------
        if hz == 20:
            print()
            print("  F  TRENNSCHAERFE — welcher gepflanzte Effekt wird "
                  "gefunden?")
            for staerke in (0.2, 0.5, 1.0, 2.0):
                u, _o = gruppen(je, "q_auf", 2, pflanze=staerke)
                b = band(u, block)
                gef = b and b[1] > 0
                print("     %+.1f Punkte gepflanzt -> gemessen %+.3f "
                      "[%+.3f .. %+.3f]  %s"
                      % (staerke, b[0], b[1], b[2],
                         "✔ gefunden" if gef else "nicht gefunden"))

        # --- B: beide Historienhaelften --------------------------------
        if hz == 20:
            print()
            print("  C  BEIDE HISTORIENHAELFTEN (Schnitt A)")
            tage = sorted(je)
            mitte = tage[len(tage) // 2]
            for lab, teil in (("erste", {t: z for t, z in je.items()
                                         if t < mitte}),
                              ("zweite", {t: z for t, z in je.items()
                                          if t >= mitte})):
                u, o = gruppen(teil, "q_auf", 2)
                bu, bo = band(u, block), band(o, block)
                if not bu or not bo:
                    print("     %-8s zu wenige Tage" % lab)
                    continue
                print("     %-8s unten %+7.3f [%+.3f .. %+.3f] · "
                      "oben %+7.3f [%+.3f .. %+.3f]"
                      % (lab, bu[0], bu[1], bu[2], bo[0], bo[1], bo[2]))

        # --- G: SCHALTER statt Regler -----------------------------------
        # ⚠️ NACH DEM PRAEZEDENZFALL H-4c: `oi_aenderung` traegt "als
        # SCHALTER statt Regler - die Monotonie fiel". Wenn eine Groesse als
        # REGEL wirkt, aber keine Stufenordnung hat, ist die Trichterstufe
        # die richtige Bauform. Das ist zu MESSEN, nicht zu vermuten.
        print()
        print("  G  SCHALTER STATT REGLER — wirkt `turnover` als REGEL?")
        print("     (dieselbe Basis: aufgeloest, echte Geometrie, H%d)" % hz)
        print("     %-24s %10s %24s  %s"
              % ("Regel", "Punkte", "Band", "Kontrolle"))
        for lab, sch in (("sperre oberstes 1/5", 4),
                         ("sperre oberste 2/5", 3),
                         ("sperre obere 3/5", 2)):
            def regel(mische=None, s2=sch):
                aus = {}
                for tag, z0 in je.items():
                    z = [x for x in z0 if x["q_auf"] is not None]
                    if len(z) < MIN_JE_TAG:
                        continue
                    w = np.array([x["kennzahl"] for x in z], float)
                    y = np.array([x["q_auf"] for x in z], float)
                    r = W.rang(w)
                    if mische is not None:
                        r = mische.permutation(r)
                    f = np.minimum((r * 5).astype(int), 4)
                    frei = f < s2
                    if frei.sum() < 3 or (~frei).sum() < 1:
                        continue
                    aus[tag] = 100.0 * (float(y[frei].mean())
                                        - float(y.mean()))
                return aus
            b = band(regel(), block)
            if not b:
                print("     %-24s zu wenige Tage" % lab)
                continue
            k = kontrolle(lambda r, f=regel: f(r), b[0], block)
            print("     %-24s %+10.3f [%+.3f .. %+.3f]  %d/%d %s"
                  % (lab, b[0], b[1], b[2], k, MISCHUNGEN,
                     "✔ TRAEGT" if traegt(b, k) else ""), flush=True)

        if hz == 20 and beste:
            lab, bu, bo, sch, ku, ntage = beste
            print()
            print("  " + "=" * 96)
            print("  DIE NEUE TABELLE — Schnitt %s" % lab.strip())
            su = schrumpfe_zu_neutral(bu[0], ntage, 0.0, PSEUDO_STICHPROBE)
            so = schrumpfe_zu_neutral(bo[0], ntage, 0.0, PSEUDO_STICHPROBE)
            stufen = tuple(round(su["gewichtet"], 2) if i < sch
                           else round(so["gewichtet"], 2) for i in range(5))
            print("    stufen=(%s),"
                  % ", ".join("%+.2f" % x for x in stufen))
            print()
            print("    alt: (+3.15, +0.83, +0.22, -1.79, -2.40)  "
                  "Spanne 5,55 Punkte")
            print("    neu: (%s)  Spanne %.2f Punkte"
                  % (", ".join("%+.2f" % x for x in stufen),
                     max(stufen) - min(stufen)))
            print()
            print("  ⚠️ R-R9: ein Beitragswechsel verlangt die "
                  "NEUKALIBRIERUNG der Schwelle,")
            print("     `KALIBRIERT_FUER` und Befundkarte 3.9. Diese Zahlen")
            print("     sind der ERSTE Schritt, nicht der letzte.")

    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
