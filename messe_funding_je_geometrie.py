# -*- coding: utf-8 -*-
"""Aendert die GEOMETRIE das Beitragsergebnis? (25.09.2026)

Befund 2.591 hat festgestellt: die Barrierengeometrie der Messung ist nicht
die Betriebsgeometrie, und `HORIZONT_JE_LAGE[(hebel,einstieg)] = 3` ist der
Aufloesungsmedian der MESSgeometrie. Daraus folgt eine Entscheidung - und
die soll nicht abstrakt getroffen werden.

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE
═══════════════════════════════════════════════════════════════════════

    Traegt `funding` auf `barriere` auch dann, wenn man die Geometrie und
    den dazu passenden Horizont wechselt?

Drei Zellen, jede mit ihrem EIGENEN Aufloesungsmedian als Horizont
(aus 2.591 gemessen, nicht gewaehlt):

    MESSUNG   Stop min(25%K, max(5%K, 0,75 ATR))   ~6,2 %    H3
    BETRIEB   Stop 13 % des Kurses (2.397)                   H10
    RUECKFALL Stop clamp(2,5 ATR, ...)             ~20,6 %   H16

⚠️ Der Horizont ist NICHT freigestellt: er folgt je Zelle dem Punkt, an
dem rund die Haelfte der Anker aufgeloest ist. Wer ihn festhaelt,
vergleicht Geometrien bei ungleicher Aufloesung.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ WARUM DIE BARRIERE HIER LOKAL GERECHNET WIRD
═══════════════════════════════════════════════════════════════════════

`k1c_hebel_barriere.barriere_je_reihe` nimmt die Geometrie nicht als
Parameter. Sie zu erweitern hiesse, ein Modul zu aendern, an dem SECHS
Messwerkzeuge haengen - und zwar mitten in einer laufenden Messreihe.

➤ Deshalb steht die Rechnung hier, und die ERSTE Ausgabe des Werkzeugs
ist der Nachweis, dass sie mit `barriere_je_reihe` BITGLEICH ist, wenn
man ihr die Messgeometrie gibt. Ohne diesen Nachweis waere jeder
Unterschied zwischen den Zellen nicht zuzuordnen.

═══════════════════════════════════════════════════════════════════════
 DIE NORM
═══════════════════════════════════════════════════════════════════════

Nullpunkt, Perzentil und Staerken kommen aus `messnorm`. ⚠️ Die
Staerkenleiter wird nach unten verlaengert, weil `messnorm.STAERKEN` fuer
R-Einheiten gebaut ist: ihre unterste Sprosse 0,02 bedeutet auf der QUOTE
eine Spanne von 0,04 - vier Prozentpunkte, mehr als der ganze zu
erwartende Bereich. Begruendung allein aus der Skala (Quote in [0,1],
Nullstelle 0,3333).

⚠️ `ungeloest=0.0` waere die UNBEDINGTE Quote. Hier wird die BEDINGTE
gemessen (`ungeloest=None`), und das ist begruendet: die Kelly-Nullstelle
1/(1+CRV) ist die Ruinwahrscheinlichkeit OHNE Zeitgrenze, wo sich jeder
Pfad aufloest - sie IST die bedingte Quote. Gemessen (2.591): die bedingte
Quote konvergiert bei H120 auf 0,3405 bis 0,3658, die unbedingte bei H3
liegt bei 0,025 bis 0,145. Die unbedingte gegen die Nullstelle zu stellen
waere ein Einheitenfehler.

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_funding_je_geometrie.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import k1c_hebel_barriere as KB                                # noqa: E402
import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_kandidaten_als_regel as K                         # noqa: E402
import messe_beitrag_auf_auswahl as MB                         # noqa: E402
import messnorm as N                                           # noqa: E402
import messnorm_auswahl as MA                                  # noqa: E402
import messe_funding_niveau as F                                      # noqa: E402
from agent.entscheidungsrechnung import GRENZEN                 # noqa: E402

CRV = 2.0
MIND_JE_TAG = 12
STAERKEN_Q = (0.0025, 0.005, 0.01) + tuple(N.STAERKEN)

# ── Die drei Zellen. Der Horizont ist der GEMESSENE Aufloesungsmedian
#    aus 2.591, keine Wahl.
ZELLEN = (
    ("MESSUNG  ~6,2 %", 3,
     lambda k, a: min(GRENZEN["stop_max_relativ"] * k,
                      max(GRENZEN["stop_min_relativ"] * k, 0.75 * a))),
    ("BETRIEB   13 %", 10, lambda k, a: 0.13 * k),
    ("RUECKFALL ~20,6 %", 16,
     lambda k, a: min(max(2.5 * a,
                          max(GRENZEN["stop_min_relativ"] * k, 0.75 * a)),
                      GRENZEN["stop_max_relativ"] * k)),
)


def barriere_je_reihe_lokal(reihe, H, stopregel):
    """Wie `KB.barriere_je_reihe` mit ungeloest=None, aber mit waehlbarer
    Stopregel. Die Reihenfolge (Stop zuerst) ist uebernommen."""
    tage = [x[0] for x in reihe]
    c = np.array([x[1] for x in reihe], float)
    h = np.array([x[2] for x in reihe], float)
    t = np.array([x[3] for x in reihe], float)
    atr = B.spanne(h, t, c, B.SCHWANKUNG)
    aus = {}
    for i in range(len(c) - 1):
        if not np.isfinite(atr[i]) or c[i] <= 0:
            continue
        s = stopregel(c[i], atr[i])
        if s <= 0:
            continue
        stop, ziel = c[i] - s, c[i] + CRV * s
        for j in range(i + 1, min(i + 1 + H, len(c))):
            if t[j] <= stop:
                aus[tage[i]] = 0.0
                break
            if h[j] >= ziel:
                aus[tage[i]] = 1.0
                break
    return aus


def barriere_je_tag_lokal(je_tag, reihen, H, stopregel):
    je_sym = {s: barriere_je_reihe_lokal(v, H, stopregel)
              for s, v in reihen.items()}
    neu, drin, ges = {}, 0, 0
    for tag, zeilen in je_tag.items():
        z = []
        for x in zeilen:
            ges += 1
            b = (je_sym.get(x["sym"]) or {}).get(tag)
            if b is None:
                continue
            drin += 1
            z.append({"sym": x["sym"], "kennzahl": x["kennzahl"],
                      "in_r": float(b)})
        if len(z) >= MIND_JE_TAG:
            neu[tag] = z
    return neu, (drin / ges if ges else 0.0)


def _zusichere_quote(je_tag, wo):
    """⚠️⚠️ DIE ZUSICHERUNG AUF DEN DATEN, nicht auf der Absicht.

    Befund 2.590 entstand, weil der Docstring `barriere` sagte und in den
    Daten `bewegung_r` stand. Eine Zielgroesse ist eine Eigenschaft der
    WERTE. Hier bricht es ab, statt zu mahnen."""
    gesehen = set()
    for z in je_tag.values():
        for x in z:
            gesehen.add(float(x["in_r"]))
            if len(gesehen) > 4:
                break
    fremd = gesehen - {0.0, 1.0}
    if fremd:
        raise SystemExit(
            "⛔ ABBRUCH (%s): `in_r` enthaelt %r - die Zielgroesse `barriere` "
            "laesst nur 0.0 und 1.0 zu. Das ist der Fehler von Befund 2.590."
            % (wo, sorted(fremd)[:5]))
    return sorted(gesehen)


def _q_je_fuenftel(je_tag, mom, anteil, tage=None):
    sammel = {k: [] for k in range(5)}
    n = 0
    for tag, z in je_tag.items():
        if tage is not None and tag not in tage:
            continue
        if len(z) < MIND_JE_TAG:
            continue
        m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
        if m is None or m.sum() < 8:
            continue
        g = [x for x, keep in zip(z, m) if keep]
        w = np.array([x["kennzahl"] for x in g], float)
        y = np.array([x["in_r"] for x in g], float)
        r = np.argsort(np.argsort(w)) / max(len(g) - 1, 1)
        drin = True
        for k in range(5):
            sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if sel.sum() < 2:
                drin = False
        if not drin:
            continue
        for k in range(5):
            sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            sammel[k].append(float(np.mean(y[sel])))
        n += 1
    if n < 30:
        return None, n
    return [float(np.mean(sammel[k])) for k in range(5)], n


def _nullpunkt(je_tag, mom, anteil, rng, zieh):
    aus = []
    for _ in range(zieh):
        sammel = {k: [] for k in range(5)}
        for tag, z in je_tag.items():
            if len(z) < MIND_JE_TAG:
                continue
            m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
            if m is None or m.sum() < 8:
                continue
            g = [x for x, keep in zip(z, m) if keep]
            y = np.array([x["in_r"] for x in g], float)
            r = rng.permutation(len(g)) / max(len(g) - 1, 1)
            for k in range(5):
                sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
                if sel.sum() >= 2:
                    sammel[k].append(float(np.mean(y[sel])))
        if all(len(sammel[k]) >= 30 for k in range(5)):
            q = [float(np.mean(sammel[k])) for k in range(5)]
            aus.append(abs(q[0] - q[4]))
    return np.array(aus)


def _trennschaerfe(je_tag, mom, anteil, rng, p90):
    aus = []
    for s in STAERKEN_Q:
        treffer, n = 0, 0
        for _ in range(10):
            sammel = {k: [] for k in range(5)}
            for tag, z in je_tag.items():
                if len(z) < MIND_JE_TAG:
                    continue
                m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if m is None or m.sum() < 8:
                    continue
                g = [x for x, keep in zip(z, m) if keep]
                y = np.array([x["in_r"] for x in g], float)
                r = rng.permutation(len(g)) / max(len(g) - 1, 1)
                for k in range(5):
                    sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4
                                          else r <= 1.0)
                    if sel.sum() >= 2:
                        sammel[k].append(float(np.mean(y[sel]))
                                         + (k - 2.0) * (s / 2.0))
            if all(len(sammel[k]) >= 30 for k in range(5)):
                q = [float(np.mean(sammel[k])) for k in range(5)]
                n += 1
                if abs(q[0] - q[4]) > p90:
                    treffer += 1
        aus.append((s, treffer / n if n else float("nan")))
    return aus


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("AENDERT DIE GEOMETRIE DAS BEITRAGSERGEBNIS?  `funding` auf "
          "`barriere`")
    print("=" * 100)
    print("  Zielgroesse barriere (bedingt, ungeloest=None) · CRV %.1f" % CRV)
    print("  Nullpunkt aus messnorm: %d Ziehungen, %.0f. Perzentil"
          % (N.NULL_ZIEHUNGEN, N.NULL_PERZENTIL))

    rng = np.random.default_rng(20260925)
    reihen = B.lade()
    if grenze:
        reihen = {k: reihen[k] for k in list(reihen)[:grenze]}
    mom = MB.momentum250(reihen)

    # ── NACHWEIS: ist die lokale Rechnung bitgleich? ──────────────────
    probe = dict(list(reihen.items())[:25])
    ab, gl, n = 0, 0, 0
    for sym, reihe in probe.items():
        a = KB.barriere_je_reihe(reihe, 3, None, None)
        b = barriere_je_reihe_lokal(reihe, 3, ZELLEN[0][2])
        for t in set(a) | set(b):
            n += 1
            if a.get(t) == b.get(t):
                gl += 1
            else:
                ab += 1
    print("  Bitgleichheit lokal gegen `KB.barriere_je_reihe` (25 Reihen, "
          "Messgeometrie/H3):")
    print("     %d von %d gleich, %d abweichend -> %s"
          % (gl, n, ab, "✔ BITGLEICH" if ab == 0 else "⛔ NICHT gleich"))
    if ab:
        return 1

    for kand in ("funding", "zufall"):
        zus = F.lade_funding() if kand == "funding" else None
        print()
        print("=" * 100)
        print("  %s" % kand)
        print("=" * 100)
        for nam, H, regel in ZELLEN:
            je = K.baue(reihen, kand, zus, horizont=H)
            if not je:
                print("    %-20s leere Welt" % nam)
                continue
            je, ant = barriere_je_tag_lokal(je, reihen, H, regel)
            if not je:
                print("    %-20s keine Barrieren-Welt" % nam)
                continue
            werte = _zusichere_quote(je, "%s/%s" % (kand, nam))
            print()
            print("    ── %-20s H%-3d · %5.1f %% der Anker aufgeloest · "
                  "Werte %s" % (nam, H, 100 * ant, werte))
            for menge in MA.zulaessige_mengen(je, mom, horizont=H):
                anteil = MA.MENGEN[menge]
                q, n_t = _q_je_fuenftel(je, mom, anteil)
                if q is None:
                    print("       Menge %-5s zu wenige Tage (%d)"
                          % (menge, n_t))
                    continue
                spanne = abs(q[0] - q[4])
                null = _nullpunkt(je, mom, anteil, rng, N.NULL_ZIEHUNGEN)
                p90 = (float(np.percentile(null, N.NULL_PERZENTIL))
                       if len(null) >= 10 else float("nan"))
                auf = all(q[i] <= q[i + 1] for i in range(4))
                ab_ = all(q[i] >= q[i + 1] for i in range(4))
                print("       Menge %-5s (%d Tage)" % (menge, n_t))
                print("          q        %s"
                      % " ".join("%7.4f" % x for x in q))
                print("          Punkte   %s"
                      % " ".join("%7.3f" % (100 * (x - float(np.mean(q))))
                                 for x in q))
                print("          B5 %s · Spanne %.4f · Nullpunkt-Perz %.4f "
                      "-> %s"
                      % ("steigend ✔" if auf else "fallend ✔" if ab_
                         else "NICHT monoton",
                         spanne, p90,
                         "UEBER" if spanne > p90 else "⛔ IM RAUSCHEN"))
                ueber = [i for i, x in enumerate(q) if x > 1.0 / (1 + CRV)]
                print("          Kelly-Nullstelle %.4f · darueber: %s"
                      % (1.0 / (1 + CRV), ueber or "⛔ KEINES"))
                if np.isfinite(p90) and menge == "frei":
                    ts = _trennschaerfe(je, mom, anteil, rng, p90)
                    gef = next((s for s, q_ in ts if q_ >= 0.8), None)
                    print("          Trennschaerfe %s"
                          % "  ".join("%.4f:%.0f%%" % (s, 100 * q_)
                                      for s, q_ in ts))
                    if gef:
                        print("          ➤ Aufloesung: Staerke %.4f = Spanne "
                              "%.4f · gemessene Spanne %.4f -> %s"
                              % (gef, 2 * gef, spanne,
                                 "UEBER der Aufloesung"
                                 if spanne > 2 * gef
                                 else "⛔ UNTER der Aufloesung (Grauzone)"))
                    else:
                        print("          ➤ Aufloesung: keine Staerke "
                              "zuverlaessig gefunden")
    print()
    print("  ⚠️ DIE ENTSCHEIDUNGSREGEL, vorab: traegt `funding` in ALLEN")
    print("     drei Zellen, ist die Geometriewahl fuer diesen Beitrag")
    print("     gleichgueltig. Traegt es nur in EINER, haengt der Befund")
    print("     an der Geometrie - und dann ist die Wahl zu entscheiden,")
    print("     bevor weiter gemessen wird.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
