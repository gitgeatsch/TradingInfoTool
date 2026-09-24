# -*- coding: utf-8 -*-
"""WELCHE VOLA-LAGE IST FUER DEN HEBEL OPTIMAL? (Hypothese H-vola)

## Die Vorabfestlegung - vor der Messung geschrieben

Nutzervorstellung (24.09.), die die Frage praezise macht:

    1  Spot/Hebel Einstieg  -> die RICHTUNG
    2  wenn die Lage passt UND vola zur Lage passt, koennte sich der
       Hebel ergeben -> HOEHE und RISIKO
    3  Frage: WELCHE VOLA IST OPTIMAL?

Dazu die Hypothese H-vola (`Basisinfos/Hypothese_vola_als_Geometriegroesse_
24_09.md`): `vola` ist kein Richtungsbeitrag (N-52 widerlegt das) sondern
die GEOMETRIEgroesse - es sagt vorher, OB ein Trade ueberhaupt aufgeloest
wird (+3,1 Punkte Aufloesungsquote, groesster sauberer Effekt).

## Die zwei Fragen, getrennt gehalten

    A  INTERAKTION   Traegt `turnover` INNERHALB der vola-Schichtung
                     staerker? N1-D fand +0,02217 am 06.09. - VOR dem
                     Messstandard. Hier auf dem heutigen Stand.
    B  OPTIMUM       Welche vola-Lage traegt den Hebel am ehesten? Dafuer
                     zaehlen DREI Groessen je Lage:
                        Aufloesungsquote  wie oft wird ueberhaupt entschieden
                        Trefferquote      der ENTSCHIEDENEN
                        Kelly             daraus, gegen 1/(1+CRV)

## ⚠️⚠️ WARUM DIE AUFLOESUNGSQUOTE ZAEHLT

Ein Trade, der weder Ziel noch Stop erreicht, zaehlt in der
Barrieren-Rechnung als NIETE - obwohl er nicht verloren hat. N10 hat
gemessen: bei H20 bleiben 7,39 % offen, bei H5 sogar 42,86 %. Wer den
Hebel an die Barrieren-Quote haengt, bestraft also unaufgeloeste Trades.
`vola` sagt vorher, welche das sind.

## Die Entscheidungsregel - vorab

    A traegt     turnover ist in mindestens einer vola-Lage BELEGT
                 staerker als im Schnitt -> die Interaktion ist real
    A traegt nicht  kein Unterschied ueber die Baender -> N1-D war ein
                 Artefakt der alten Regeln, die Kombination faellt
    B Optimum    gibt es eine vola-Lage, in der Kelly BELEGT ueber der
                 Nullstelle liegt? Nur dann ist ein Hebel dort
                 gerechtfertigt
    ⛔ keine     liegt in KEINER Lage Kelly belegt darueber, ist auch
                 ueber vola kein Hebel zu rechtfertigen

⚠️ MEHRFACHTEST: 5 vola-Lagen. Erwartung wird gerechnet, nicht geschaetzt.

⚠️ NUR LESEND.

    python phase4_vola_als_geometrie.py
    python phase4_vola_als_geometrie.py --menge 20%
    python phase4_vola_als_geometrie.py --quelle frei
    python phase4_vola_als_geometrie.py --horizont 5   (nahe der echten
                                        Haltedauer von rund 3 Tagen)
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertung_kalibrierung as KAL                   # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402
import messnorm                                              # noqa: E402
import phase3_reproduktion as R3                             # noqa: E402

CRV = 2.0
# ⚠️⚠️⚠️ DIE BLOCKLAENGE KOMMT AUS DER NORM, NICHT AUS EINER SETZUNG.
#
# Die erste Fassung schrieb BLOCK = 90 fuer JEDEN Horizont. Die Norm sagt
# `messnorm._block(H) = max(15, 3 x H)` - also 15 bei H5, 60 bei H20, 180
# bei H60. Bei H5 war mein Block damit SECHSMAL zu lang (Band zu breit,
# echte Effekte uebersehen), bei H60 zu kurz (Band zu eng, Fehlalarme).
#
# ⚠️ Und die Norm verlangt mehr als das Setzen: *"die Blocklaenge wird je
# Messung NACHGEPRUEFT (`pruefe_block`), nicht angenommen. Wer sie nur
# setzt, hat sie geraten."* Genau das hatte ich getan.
BLOCK = None          # wird in main() aus dem Horizont gesetzt
ZIEHUNGEN = 400
MIN_ANKER = 500


def vola_je_tag(reihen: dict, horizont: int = 20) -> dict:
    """{tag: {sym: 0..4}} - ATR relativ zum eigenen 250-Tage-Median, dann
    im TAGESQUERSCHNITT gerangt.

    ⚠️ Genau die Definition aus dem Kandidatenblatt: *"eigene ATR relativ
    zum eigenen 250-Tage-Median, dann im Tagesquerschnitt gerangt"*. Die
    Eigennormierung ist der Punkt - ohne sie raengte man Assetklassen
    statt Lagen.
    """
    roh: dict = defaultdict(dict)
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t_ = np.array([x[3] for x in z], float)
        spanne = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(250, len(c) - horizont):
            fen = spanne[i - 250:i]
            fen = fen[np.isfinite(fen) & (fen > 0)]
            if len(fen) < 100 or not np.isfinite(spanne[i]) or spanne[i] <= 0:
                continue
            med = float(np.median(fen))
            if med <= 0:
                continue
            roh[tage[i]][sym] = spanne[i] / med
    aus = {}
    for tag, d in roh.items():
        if len(d) < 12:
            continue
        syms = list(d)
        w = np.array([d[s] for s in syms], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        aus[tag] = {s: min(int(x * 5), 4) for s, x in zip(syms, r)}
    return aus


def sammle(menge, quelle, reihen, zeilen, tage_je_sym):
    """{(vola, turnover): {tag: [(entschieden, treffer), ...]}}"""
    erlaubt = KAL.erlaubte_anker(reihen, menge)
    vo5 = vola_je_tag(reihen)
    tu5 = KAL._fuenftel_je_tag(K.baue(reihen, "turnover",
                                      R3._zusatz("turnover", quelle),
                                      horizont=20))
    fu5 = KAL._fuenftel_je_tag(K.baue(reihen, "funding", F.lade_funding(),
                                      horizont=20))
    aus: dict = defaultdict(lambda: defaultdict(list))
    for z in zeilen:
        sym, i = z["sym"], z["i"]
        tg = tage_je_sym.get(sym)
        if not tg or i >= len(tg):
            continue
        tag = tg[i]
        if erlaubt is not None and (tag, sym) not in erlaubt:
            continue
        v = vo5.get(tag, {}).get(sym)
        if v is None:
            continue
        w = z.get(KAL.VARIANTE)
        # ⚠️ DREI Zustaende, nicht zwei: Ziel / Stop / OFFEN. Die offenen
        # sind der Kern der Hypothese und duerfen nicht wegfallen.
        if w is None:
            ent, tr = 0, 0
        elif abs(w - CRV) < 1e-9:
            ent, tr = 1, 1
        elif abs(w + 1.0) < 1e-9:
            ent, tr = 1, 0
        else:
            ent, tr = 0, 0
        t = tu5.get(tag, {}).get(sym)
        f = fu5.get(tag, {}).get(sym)
        aus[v][tag].append((ent, tr, t, f))
    return {k: dict(v) for k, v in aus.items()}


def band(je_tag, wert_fn, rng):
    """Blockbootstrap ueber Kalendertage auf eine Quote."""
    tage = sorted(je_tag)
    if len(tage) < BLOCK + 10:
        return (float("nan"),) * 3
    p = wert_fn(tage)
    if p is None:
        return (float("nan"),) * 3
    starts = np.arange(len(tage) - BLOCK + 1)
    anzahl = int(np.ceil(len(tage) / BLOCK))
    z = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        tg = [tage[j] for s in idx
              for j in range(s, min(s + BLOCK, len(tage)))][:len(tage)]
        v = wert_fn(tg)
        if v is not None:
            z.append(v)
    if not z:
        return (float("nan"),) * 3
    return (p, float(np.percentile(z, 2.5)), float(np.percentile(z, 97.5)))


def main() -> int:
    menge = KAL._argv_wert("--menge", "frei")
    quelle = KAL._argv_wert("--quelle", "gesamt")
    # ⚠️⚠️⚠️ DER HORIZONT IST SEIT DEM 24.09. EIN SCHALTER - UND DAS WAR
    # EIN FUND AN DER EIGENEN MESSUNG.
    #
    # `messe_zielregel.HORIZONT` steht auf 60 Handelstagen. Die erste
    # Fassung dieses Werkzeugs sprach von "H20" und mass in Wahrheit ueber
    # 60 Tage - daher die Aufloesungsquote von 97,5 bis 99,8 Prozent, wo
    # N10 fuer H20 7,39 Prozent OFFENE Trades ausweist.
    #
    # ⚠️ Und der Horizont ist hier nicht beliebig: die echten
    # Hebelpositionen haben eine MEDIAN-HALTEDAUER VON 0,30 TAGEN (188
    # Positionen, 2.493), der Betrieb rechnet mit rund 3 Handelstagen
    # (2.513-horizont). Eine Bewertung ueber 60 Tage beschreibt etwas
    # anderes als den Trade, der tatsaechlich stattfindet.
    hor = int(KAL._argv_wert("--horizont", "60"))
    ZR.HORIZONT = hor
    global BLOCK
    BLOCK = messnorm._block(hor)
    print("=" * 112)
    print("WELCHE VOLA-LAGE IST FUER DEN HEBEL OPTIMAL? (H-vola)")
    print("=" * 112)
    print("  MENGE %s · QUELLE %s · CRV %.1f · HORIZONT %d Tage"
          % (menge, quelle, CRV, hor))
    print("  Blocklaenge %d = messnorm._block(%d) - aus der NORM, nicht gesetzt"
          % (BLOCK, hor))
    print("  " + messnorm.standardzeile())
    print("  Hypothese: Basisinfos/Hypothese_vola_als_Geometriegroesse_24_09.md")
    print("  ⚠️ vola = eigene ATR / eigener 250-Tage-Median, dann im")
    print("     Tagesquerschnitt gerangt (Definition aus dem Kandidatenblatt)")

    print("\n  Laden ...")
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    lagen = sammle(menge, quelle, reihen, zeilen, tage_je_sym)
    rng = np.random.default_rng(messnorm.SAAT)
    null = 1.0 / (1.0 + CRV)

    # ---- B: DIE DREI GROESSEN JE VOLA-LAGE -------------------------
    print("\n" + "-" * 112)
    print("  FRAGE B - WELCHE VOLA-LAGE? (0 = ruhigstes Fuenftel)")
    print("-" * 112)
    print("  %-6s %9s %-26s %-26s %12s"
          % ("vola", "Anker", "Aufloesungsquote", "Treffer der ENTSCHIEDENEN",
             "kelly"))
    ergebnis = {}
    for v in range(5):
        je = lagen.get(v)
        if not je:
            continue
        n = sum(len(x) for x in je.values())
        if n < MIN_ANKER:
            print("  %-6d %9d  zu wenige Anker" % (v, n))
            continue

        def q_aufl(tg, _je=je):
            a = sum(e for t in tg for e, _tr, _t, _f in _je.get(t, []))
            b = sum(len(_je.get(t, [])) for t in tg)
            return a / b if b else None

        def q_tref(tg, _je=je):
            a = sum(tr for t in tg for e, tr, _t, _f in _je.get(t, []) if e)
            b = sum(1 for t in tg for e, _tr, _t, _f in _je.get(t, []) if e)
            return a / b if b else None

        # ⚠️ DIE NORM VERLANGT DEN NACHWEIS DER BLOCKLAENGE, nicht ihre
        # Setzung: `pruefe_block` misst die Autokorrelation der
        # Tageswirkung beim Blockabstand. Ueber 0,15 ist der Block zu
        # kurz und das Band zu eng.
        _tw = {t: (sum(tr for e, tr, _t, _f in x if e)
                   / max(sum(1 for e, _tr, _t, _f in x if e), 1))
               for t, x in je.items()
               if any(e for e, _tr, _t, _f in x)}
        _bp = messnorm.pruefe_block(_tw, BLOCK)
        au, au_u, au_o = band(je, q_aufl, rng)
        tq, tq_u, tq_o = band(je, q_tref, rng)
        kelly = (tq * (1 + CRV) - 1) / CRV if np.isfinite(tq) else float("nan")
        ergebnis[v] = (n, au, au_u, au_o, tq, tq_u, tq_o, kelly)
        print("  %-6d %9d  %5.1f %% [%4.1f .. %4.1f]   %5.1f %% [%4.1f .. %4.1f]"
              "   %+.5f  %s"
              % (v, n, 100 * au, 100 * au_u, 100 * au_o,
                 100 * tq, 100 * tq_u, 100 * tq_o, kelly,
                 "Block ok (ak %+.2f)" % _bp["ak"] if _bp["ok"]
                 else "⚠ BLOCK ZU KURZ (ak %+.2f)" % _bp["ak"]))

    print("\n  Kelly-Nullstelle = %.1f %% · r_min 0,005 · r_max 0,0125"
          % (100 * null))
    # ⚠️ Die entscheidende Frage: liegt die Trefferquote der ENTSCHIEDENEN
    # in einer Lage BELEGT ueber der Nullstelle? Ein Punktwert genuegt
    # nicht - das Band muss sie ausschliessen.
    drueber = [v for v, r in ergebnis.items() if r[5] > null]
    drunter = [v for v, r in ergebnis.items() if r[6] < null]
    print("  ➤ belegt UEBER der Nullstelle: %s · belegt darunter: %s"
          % (drueber or "keine", drunter or "keine"))

    # ---- A: DIE INTERAKTION ----------------------------------------
    print("\n" + "-" * 112)
    print("  FRAGE A - TRAEGT `turnover` INNERHALB EINER VOLA-LAGE STAERKER?")
    print("       (N1-D fand +0,02217 am 06.09. - VOR dem Messstandard)")
    print("-" * 112)
    print("  %-6s %9s %14s %-26s %s"
          % ("vola", "Anker", "tu0 minus tu4", "Band", "Urteil"))
    traegt, werte, breiten = 0, [], []
    for v in range(5):
        je = lagen.get(v)
        if not je:
            continue

        def d_turn(tg, _je=je):
            a0 = b0 = a4 = b4 = 0
            for t in tg:
                for e, tr, tu, _f in _je.get(t, []):
                    if not e or tu is None:
                        continue
                    if tu == 0:
                        a0 += tr
                        b0 += 1
                    elif tu == 4:
                        a4 += tr
                        b4 += 1
            if not b0 or not b4:
                return None
            return a0 / b0 - a4 / b4

        d, u, o = band(je, d_turn, rng)
        if not np.isfinite(d):
            print("  %-6d %9s  zu wenige Anker" % (v, "-"))
            continue
        n = sum(1 for x in je.values() for e, _tr, tu, _f in x
                if e and tu in (0, 4))
        ok = u > 0 or o < 0
        traegt += int(ok)
        werte.append(d)
        breiten.append(o - u)
        print("  %-6d %9d %+13.4f [%+.4f .. %+.4f]   %s"
              % (v, n, d, u, o, "✔ TRAEGT" if ok else "⚠ Null ein"))

    # ---- DIE ENTSCHEIDUNG ------------------------------------------
    print("\n" + "=" * 112)
    print("  ENTSCHEIDUNG nach der Vorabfestlegung")
    print("=" * 112)
    if werte:
        lam = 0.05 * len(werte)
        p = 1.0 - sum(math.exp(-lam) * lam ** k / math.factorial(k)
                      for k in range(traegt))
        print("  A: turnover traegt in %d von %d vola-Lagen "
              "(Erwartung %.2f, Poisson p = %.4f)"
              % (traegt, len(werte), lam, p))
        if len(werte) > 1:
            spann = max(werte) - min(werte)
            print("     Spannweite %+.4f gegen Median-Band %+.4f"
                  % (spann, float(np.median(breiten))))
            print("     ➤ %s"
                  % ("die Lagen unterscheiden sich NICHT mehr als ihre "
                     "Fehler" if spann <= np.median(breiten) else
                     "die Lagen streuen weiter als ihre Fehler"))
    if drueber:
        print("  B: ✔ In vola-Lage(n) %s liegt die Trefferquote der")
        print("     ENTSCHIEDENEN belegt UEBER der Kelly-Nullstelle." % drueber)
        print("     ➤ Dort waere ein Hebel gerechtfertigt.")
    else:
        print("  B: ⛔ IN KEINER VOLA-LAGE liegt die Trefferquote belegt")
        print("     ueber der Kelly-Nullstelle. Auch ueber `vola` ist damit")
        print("     kein Hebel zu rechtfertigen.")
        print("     ⚠️ Das widerlegt H-vola NICHT - die Hypothese sagt, vola")
        print("        steuere die GEOMETRIE, nicht die Richtung. Sie sagt")
        print("        nicht, dass daraus ein Hebel FOLGT.")
    print("=" * 112)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
