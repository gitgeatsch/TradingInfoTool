# -*- coding: utf-8 -*-
"""N-56 — TRAEGT DIE LIVE GESCHALTETE OI-SPERRE RICHTUNG? (06.09.2026)

## Warum das der dringlichste offene Punkt ist

Das Audit vom 06.09. hat gezeigt: **alle drei Live-Registrierungen stehen
auf H20 in R** - also auf `bewegung_r`, einem Massstab, den N-52 in einer
richtungsfreien Kunstwelt hat feuern sehen (+0,04050).

    funding        H20 · +0,0246 R              `BEITRAEGE`, Gewichtung
    turnover       H20 · +0,0616 R              `BEITRAEGE`, Gewichtung
    oi_aenderung   H20 · +0,0145 R              `rollen_gate` - eine SPERRE

⚠️ `oi_aenderung` ist der dringlichste Fall: es ist die einzige der drei,
die **Signale vollstaendig unterdrueckt** statt sie nur zu gewichten. Eine
Sperre auf ungepruefter Grundlage kostet Gelegenheiten, ohne dass es
jemand sieht.

⚠️⚠️ Und N-53 hat das NICHT beantwortet: dort wurde bei **H5 auf der
Barrieren-Quote** gemessen. Das ist eine andere Basis - nach R-R11 darf
daraus weder Bestaetigung noch Widerlegung abgeleitet werden.

## Der Aufbau — drei Stufen, in dieser Reihenfolge

    1  REPRODUKTION (R-R11)   `bewegung_r` bei H20, oberstes Fuenftel
       gesperrt. Kommen +0,0145 / +0,0246 / +0,0616 R zurueck?
       ⚠️ OHNE das gilt nichts weiter. Wer die Basis aendert und ein
          anderes Ergebnis bekommt, hat nichts widerlegt.

    2  IST DIE BASIS KONTAMINIERT?   dieselbe Messung in einer
       richtungsfreien Kunstwelt. Feuert `bewegung_r` auch dort, steht
       die Registrierung auf Sand - unabhaengig davon, was sie zeigt.

    3  RICHTUNGSREIN   GS bei H20: symmetrische Barrieren, nur
       aufgeloeste Anker. Nullpunkt vorab herleitbar bei 0,5.

## ⚠️ Die FORM wird von der Live-Regel uebernommen

`oi_aenderung` sperrt live das **oberste Fuenftel** (`rollen_gate`, Stufe
terminmarkt, nur `einstieg`, nicht bei Bestand). Genau diese Form wird
gemessen - nicht das Drittel aus N-53. Eine Reproduktion, die eine andere
Regel misst, ist keine.

    python n56_oi_richtungsrein.py --probe
    python n56_oi_richtungsrein.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
from n52_vola_geometrieprobe import (band, traegt,           # noqa: E402
                                     _ausgang, MISCHUNGEN)

CRV, BRUCH = 2.0, 5.0
FAECHER = 5                    # ⚠️ wie die Live-Regel: oberstes FUENFTEL
HORIZONTE = (20, 5)            # H20 = Registrierungsbasis · H5 = Betrieb
# ⚠️ Die registrierten Werte - Ziel der Reproduktion (R-R11)
REGISTRIERT = {"oi_aenderung": 0.0145, "funding": 0.0246, "turnover": 0.0616}


def baue(reihen, zusatz, hz):
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        kaputt = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        if not je_sym:
            continue
        for i in range(B.SCHWANKUNG, len(c) - hz):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if kaputt[i:i + hz].any():
                continue
            w = je_sym.get(tage[i])
            if w is None:
                continue
            roh = _ausgang(c, h, t, i, float(br[i]), CRV, hz)
            symm = _ausgang(c, h, t, i, float(br[i]), 1.0, hz)
            je_tag.setdefault(tage[i], []).append({
                "kennzahl": float(w),
                # ⚠️ DIE REGISTRIERUNGSBASIS: Rendite in R der 1-ATR-Weite
                "bewegung_r": float((c[i + hz] - c[i]) / br[i]),
                "g0": 1.0 if roh > 0 else 0.0,
                "auf": 0.0 if roh == 0 else 1.0,
                "gs": (1.0 if symm > 0 else 0.0) if symm != 0 else None})
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def regel(je_tag, feld, mische=None):
    """Die LIVE-Regel: das oberste Fuenftel sperren, den Rest behalten."""
    aus = {}
    for tag, z0 in je_tag.items():
        z = [x for x in z0 if x[feld] is not None]
        if len(z) < FAECHER * 3:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * FAECHER).astype(int), FAECHER - 1)
        frei = f < FAECHER - 1
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        aus[tag] = float(y[frei].mean()) - float(y.mean())
    return aus


def kontrolle(je_tag, feld, echt):
    tr = 0
    for k in range(MISCHUNGEN):
        rng = np.random.default_rng(93000 + k)
        b = band(regel(je_tag, feld, mische=rng))
        if b and abs(b[0]) >= abs(echt):
            tr += 1
    return tr


def zeige(je_tag, name, hz, ziel=None):
    print()
    print("  %s bei H%d  (%d Tage, %d Anker)"
          % (name.upper(), hz, len(je_tag),
             sum(len(z) for z in je_tag.values())))
    print("     %-26s %10s %24s  %s"
          % ("Massstab", "Regel", "Band", "Kontrolle"))
    erg = {}
    for feld, lab in (("bewegung_r", "R  bewegung_r (REGISTRIERT)"),
                      ("g0", "G0 Barrieren-Quote"),
                      ("gs", "GS richtungsrein"),
                      ("auf", "AUF Aufloesungsquote")):
        b = band(regel(je_tag, feld))
        if not b:
            print("     %-26s   zu wenige Tage" % lab)
            continue
        k = kontrolle(je_tag, feld, b[0])
        tr = traegt(b, k)
        extra = ""
        if feld == "bewegung_r" and ziel is not None:
            extra = "   registriert %+.4f -> %s" % (
                ziel, "✔ REPRODUZIERT" if b[1] <= ziel <= b[2]
                else "⚠️ NICHT im Band")
        print("     %-26s %+9.5f [%+.5f .. %+.5f]  %d/%d %s%s"
              % (lab, b[0], b[1], b[2], k, MISCHUNGEN,
                 "✔" if tr else "", extra), flush=True)
        erg[feld] = (b[0], b[1], b[2], tr)
    return erg


def kunstwelt(art, hz, tage=1400, symbole=45, saat=1414):
    """Zufallslauf mit Vola-Clustern, KEINE Richtung.

    art = "rauschen"  Kennzahl ohne jeden Bezug
        = "vola"      Kennzahl bildet die Volatilitaet ab
    """
    rng = np.random.default_rng(saat)
    reihen, zusatz = {}, {}
    for s in range(symbole):
        lv = np.zeros(tage)
        for i in range(1, tage):
            lv[i] = 0.97 * lv[i - 1] + rng.normal(0, 0.10)
        vol = 0.0428 * np.exp(lv)
        c = np.empty(tage)
        c[0] = 100.0
        for i in range(1, tage):
            c[i] = c[i - 1] * float(np.exp(rng.normal(0, vol[i])
                                           - 0.5 * vol[i] ** 2))
        sp = c * vol
        h = c + np.abs(rng.normal(0, 1.24, tage)) * sp
        t = c - np.abs(rng.normal(0, 1.24, tage)) * sp
        nam = "K%02d" % s
        reihen[nam] = [(("2020-01-01_%04d" % i), c[i], h[i], t[i], 1.0)
                       for i in range(tage)]
        w = (rng.normal(0, 1, tage) if art == "rauschen"
             else vol * (1.0 + rng.normal(0, 0.05, tage)))
        zusatz[nam] = {("2020-01-01_%04d" % i): float(w[i])
                       for i in range(tage)}
    return reihen, zusatz


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-56 — traegt die LIVE geschaltete OI-Sperre RICHTUNG?")
    print("=" * 96)

    if "--probe" in sys.argv:
        ok = True
        for art, erwartung in (("rauschen", "NICHTS darf tragen"),
                               ("vola", "R und G0 duerfen feuern, GS NICHT")):
            r, z = kunstwelt(art, 20)
            e = zeige(baue(r, z, 20), "KUNSTWELT %s" % art.upper(), 20)
            if art == "rauschen":
                schuldig = [f for f in ("bewegung_r", "g0", "gs", "auf")
                            if e.get(f, (0, 0, 0, False))[3]]
                if schuldig:
                    print("     ⚠️ feuert im Leeren: %s" % ", ".join(schuldig))
                    ok = False
                else:
                    print("     ✔ nichts feuert bei reinem Rauschen")
            else:
                if e.get("bewegung_r", (0, 0, 0, False))[3]:
                    print("     ⚠️⚠️ BELEGT: `bewegung_r` - die "
                          "REGISTRIERUNGSBASIS - feuert bei einer Kennzahl,")
                    print("        die nur die Volatilitaet abbildet "
                          "(%+.5f). Das ist der Nachweis, dass die Basis"
                          % e["bewegung_r"][0])
                    print("        kontaminiert ist.")
                else:
                    print("     ⚠️ `bewegung_r` feuert NICHT - dann ist die "
                          "Basis bei H20 vielleicht doch sauber, und die")
                    print("        Audit-Vermutung waere zu voreilig gewesen.")
                if e.get("gs", (0, 0, 0, False))[3]:
                    print("     ⚠️⚠️ GS feuert ebenfalls - dann taugt es hier "
                          "nicht als Schiedsrichter.")
                    ok = False
                else:
                    print("     ✔ GS bleibt stumm - es taugt als "
                          "Schiedsrichter")
        print()
        print("     %s" % ("Der Test darf auf die echten Daten." if ok
                           else "⚠️ NICHT auf die echten Daten."))
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 0 if ok else 1

    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    tm = K.lade_terminmarkt()
    quellen = (("oi_aenderung", tm["oi_aenderung"]),
               ("funding", F.lade_funding()),
               ("turnover", MB.reihe("data/onchain_historie.db", "splycur")))
    alle = {}
    for hz in HORIZONTE:
        for name, q in quellen:
            alle[(name, hz)] = zeige(baue(reihen, q, hz), name, hz,
                                     REGISTRIERT.get(name) if hz == 20 else None)

    print()
    print("=" * 96)
    print("DIE ZUSAMMENSCHAU")
    print("=" * 96)
    print("     %-14s %-4s %11s %11s %11s   %s"
          % ("Groesse", "H", "R (regist.)", "GS (Rchtg)", "AUF (Kanal)",
             "Urteil"))
    for hz in HORIZONTE:
        for name, _q in quellen:
            e = alle[(name, hz)]
            r = e.get("bewegung_r", (0.0, 0, 0, False))
            g = e.get("gs", (0.0, 0, 0, False))
            a = e.get("auf", (0.0, 0, 0, False))
            if g[3] and g[0] > 0:
                u = "✔ traegt RICHTUNG"
            elif g[3]:
                u = "⚠️ Richtung INVERS"
            elif a[3]:
                u = "⚠️ nur der Kanal"
            else:
                u = "⚠️ keine Richtung nachweisbar"
            print("     %-14s %-4d %+11.5f %+11.5f %+11.5f   %s"
                  % (name, hz, r[0], g[0], a[0], u))
    print()
    print("  ⚠️ GS entscheidet. `bewegung_r` ist die Registrierungsbasis -")
    print("     sie wird gezeigt, damit die Reproduktion nachvollziehbar")
    print("     ist, nicht weil sie ein gueltiges Urteil traegt.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
