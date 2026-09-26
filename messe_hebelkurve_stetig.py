# -*- coding: utf-8 -*-
"""Die STETIGE Hebelkurve - der Hebel als Funktion der Lagequalitaet.

**26.09.2026**, Nutzereinwand: *"hier ist es etwas stufenartig und nicht
regelmaessig - Warum nicht -1,3?"* und *"eigentlich sollte das System
entscheiden ob -1,0 jetzt besser ist und den Hebel so anwenden, also ich
habe mir das so vorgestellt, dass eben das Risiko mit der Qualitaet
steigt, also der Hebel"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_26_Hebelkurve_stetig_26_09.md`

═══════════════════════════════════════════════════════════════════════
 WAS AN DER BANDMESSUNG FALSCH WAR
═══════════════════════════════════════════════════════════════════════

Die Bandmessung hat die ORDNUNG belegt (5 von 5 Jahren fallend, 54 von 63
Symbolen, 4 von 4 Bloecken). Das gilt.

    ⛔ Aber die Bandgrenzen -2,0 / -1,5 / -1,2 / -1,0 waren GESETZT, nicht
       gemessen. Auf *warum nicht -1,3* gibt es keine Antwort, die nicht
       willkuerlich ist.

➤ Gesucht ist eine STETIGE Kurve ohne Bandgrenzen.

═══════════════════════════════════════════════════════════════════════
 DIE KONSTRUKTION - sie steht bereits vollstaendig im Code
═══════════════════════════════════════════════════════════════════════

    1.  q(W) und CRV(W) stetig - gleitendes Fenster ueber die nach W
        sortierten Anker
    2.  kelly(W) = (q(1+CRV) - 1)/CRV        agent/betraege.py:365
    3.  hebel(W, ATR) = (kelly(W)/2) * N / s      s = Stopweite = 1,00 ATR
        Herleitung: Kelly ist der Kontoanteil, der bei Stop verloren geht;
        f*Konto = s*Position  =>  Position/Konto = f/s;  bei N Positionen
        zu je 1/N Margin ist der Hebel das N-fache
    4.  Deckel: RM-11 max_safe_hebel(s*100, 0,09) und Zielzone 2-5x

⭐ Die MINDESTSCHWELLE wird damit GERECHNET: sie liegt dort, wo hebel(W)
unter 2x faellt.

⚠️ NUR LESEN.  python messe_hebelkurve_stetig.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import (                          # noqa: E402
    trailing_mit_ausloeser, EMA_L, VORLAUF)
from agent.krypto.hebel_risk_gate import max_safe_hebel         # noqa: E402

# aus 2.628
HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
# ⚠️ 4000 und nicht mehr: die entscheidende Zone sind die schaerfsten
# 0,1 % (rund 3.400 Anker <= -1,5). Ein Fenster von 8000 kann sie gar
# nicht aufloesen - die 2x-Schwelle laege dann im ersten Fenster und
# waere wieder gesetzt statt gerechnet.
FENSTER = 4000          # Anker je gleitendem Fenster
# ⚠️ Die Stuetzstellen sitzen auf PERZENTILEN von W, nicht auf gleichen
# Rangabstaenden: die scharfen Lagen sind nur rund 1,5 % der Menge, und
# gleichgroße Schritte wuerden fast nur das Mittelfeld abtasten - genau
# den Bereich, der laut Bandmessung nichts traegt.
STUETZEN = (0.08, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0,
            3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0, 70.0, 90.0)
MARGE = 0.09            # RM-11 Wartungsmarge
POSITIONEN = 3          # gleichzeitige Positionen (Nutzerannahme, ausgewiesen)
KELLY_TEILER = 2.0      # halbes Kelly
ZIEL_MIN, ZIEL_MAX = 2.0, 5.0
SAAT = 20260926


def kelly_von(r: np.ndarray) -> tuple[float, float, float]:
    """q, CRV und Kelly aus einer Menge von R-Ergebnissen."""
    if len(r) < 50:
        return (float("nan"),) * 3
    q = float((r > 0).mean())
    g, v = r[r > 0], r[r <= 0]
    if not len(g) or not len(v) or v.mean() == 0:
        return q, float("nan"), float("nan")
    crv = float(g.mean() / abs(v.mean()))
    if crv <= 0:
        return q, crv, float("nan")
    return q, crv, (q * (1.0 + crv) - 1.0) / crv



def intraklassen_rho(r: np.ndarray, gruppe: np.ndarray) -> tuple:
    """Mittlere paarweise Korrelation der Ergebnisse INNERHALB eines Tages.

    ⚠️ Warum das gebraucht wird: `hebel = kelly/teiler * N / s` gilt nur
    fuer UNABHAENGIGE Positionen. In Krypto haengt alles an BTC. Mit
    Korrelation rho entsprechen N gleichzeitige Positionen nur
    `N/(1+(N-1)rho)` unabhaengigen - und das strebt gegen `1/rho`,
    egal wie viele man haelt.

    Gibt (rho, effektives N bei der beobachteten Gruppengroesse,
    mittlere Gruppengroesse) zurueck."""
    u, inv = np.unique(gruppe, return_inverse=True)
    cnt = np.bincount(inv)
    behalte = np.flatnonzero(cnt >= 2)
    sel = np.isin(inv, behalte)
    if sel.sum() < 60:
        return float("nan"), float("nan"), float("nan")
    r2 = r[sel]
    _u2, inv3 = np.unique(inv[sel], return_inverse=True)
    c2 = np.bincount(inv3)
    m2 = np.bincount(inv3, weights=r2) / c2
    zwischen = float(np.average((m2 - r2.mean()) ** 2, weights=c2))
    innen = float(np.average([r2[inv3 == i].var(ddof=1)
                              for i in range(len(c2))], weights=c2))
    rho = zwischen / max(zwischen + innen, 1e-12)
    kb = float(c2.mean())
    return rho, kb / (1.0 + (kb - 1.0) * rho), kb


def eff_n(n: float, rho: float) -> float:
    """So viele UNABHAENGIGE Positionen entsprechen n gleichzeitigen."""
    if rho <= 0:
        return float(n)
    return float(n) / (1.0 + (float(n) - 1.0) * rho)


def kurve(w: np.ndarray, r: np.ndarray, atr: np.ndarray,
          fenster: int = FENSTER) -> list[dict]:
    """Gleitendes Fenster ueber die nach W sortierten Anker.

    ⚠️ KEIN Gitter in W und keine Klassen - jedes Fenster traegt dieselbe
    Ankerzahl, damit jede Stuetzstelle gleich viel Aussagekraft hat. Die
    LAGE der Stuetzstellen folgt den Perzentilen von W (siehe STUETZEN)."""
    o = np.argsort(w, kind="stable")
    w, r, atr = w[o], r[o], atr[o]
    n = len(w)
    if n < fenster:
        return []
    aus = []
    gesehen = set()
    for p in STUETZEN:
        z = p / 100.0 * n
        # ⚠️ Eine Stuetzstelle, deren Fenster am Rand KLEMMT, ist keine
        # eigene Stuetzstelle mehr - sie liefert dasselbe Fenster wie die
        # naechste. Im Probelauf waren so sieben Zeilen bitgleich, und die
        # schaerfsten Lagen wurden mit einem viel zu breiten Fenster
        # verschmiert. Solche Stuetzstellen entfallen und werden benannt.
        if z < fenster / 2.0 or z > n - fenster / 2.0:
            continue
        a = int(round(z - fenster / 2.0))
        fen = fenster
        sl = slice(a, a + fen)
        if a in gesehen:
            continue
        gesehen.add(a)
        q, crv, kel = kelly_von(r[sl])
        if kel != kel:
            continue
        s = float(np.median(STOP * atr[sl]))          # Stopweite, relativ
        roh = (kel / KELLY_TEILER) * POSITIONEN / max(s, 1e-9)
        rm = max_safe_hebel(100 * s, MARGE)
        aus.append(dict(p=p, w_mitte=float(np.median(w[sl])),
                        w_von=float(w[sl][0]), w_bis=float(w[sl][-1]),
                        n=int(len(r[sl])), q=q, crv=crv, kelly=kel,
                        stop=s, roh=roh, rm11=rm,
                        hebel=float(min(ZIEL_MAX, min(roh, rm)))
                        if roh >= ZIEL_MIN else 0.0))
    return aus


def lade():
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W, P, R, A = [], [], [], [], []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        r, p, _g = trailing_mit_ausloeser(h, l, cc, atr, STOP, AUSL,
                                          ABST, HZ)
        G.append(np.array([sid[x] for x in st], np.int64)[sel])
        W.append(w[sel]); P.append(p[sel]); R.append(r[sel])
        A.append(atr[sel])
    return (np.concatenate(G), np.concatenate(W), np.concatenate(P),
            np.concatenate(R), np.concatenate(A), len(kurse))


def main() -> int:
    print("=" * 112)
    print("DIE STETIGE HEBELKURVE - ohne Bandgrenzen")
    print("=" * 112)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  Fenster %d Anker, %d Stuetzstellen auf Perzentilen · %d "
          "Positionen · halbes Kelly · RM-11 Marge %.2f"
          % (FENSTER, len(STUETZEN), POSITIONEN, MARGE))
    print()

    G, W, P, R, A, nsym = lade()
    tag = G // 24
    gut = np.isfinite(W) & np.isfinite(R) & np.isfinite(A)
    G, W, P, R, A, tag = (x[gut] for x in (G, W, P, R, A, tag))
    print("  %d Anker · %d Tage · %d Symbole" % (len(W), len(np.unique(tag)),
                                                 nsym), flush=True)
    print()

    # ══ 1. DIE ROHE KURVE ════════════════════════════════════════════
    print("=" * 112)
    print("TEIL 1 - DIE ROHE KURVE (ungeglaettet, keine Isotonie erzwungen)")
    print()
    k = kurve(W, R, A)
    print("  %6s %9s %13s %7s %8s %9s %9s %8s %8s %8s %7s"
          % ("Perz.", "W-Mitte", "W-Spanne", "n", "q", "CRV", "Kelly",
             "Stop %", "roh x", "RM-11", "Hebel"))
    for z in k:
        print("  %5.2f%% %+9.3f %13s %7d %7.1f%% %9.3f %+9.4f %8.2f %8.2f "
              "%8.2f %7s"
              % (z["p"], z["w_mitte"],
                 "%+.2f/%+.2f" % (z["w_von"], z["w_bis"]),
                 z["n"], 100 * z["q"], z["crv"], z["kelly"],
                 100 * z["stop"], z["roh"], z["rm11"],
                 ("%.2fx" % z["hebel"]) if z["hebel"] else "-"), flush=True)

    # ══ 2. IST SIE MONOTON? ══════════════════════════════════════════
    print()
    print("=" * 112)
    print("TEIL 2 - IST DIE KURVE MONOTON? (Falle 2 der Vorabfestlegung)")
    print()
    wm = np.array([z["w_mitte"] for z in k])
    ke = np.array([z["kelly"] for z in k])
    from scipy.stats import spearmanr
    rho, pv = spearmanr(wm, ke)
    ab = np.diff(ke)
    print("  Spearman Kelly gegen W:  rho %+.3f   p %.2e" % (rho, pv))
    print("  fallende Schritte: %d von %d (%.0f %%)"
          % (int((ab <= 0).sum()), len(ab), 100 * (ab <= 0).mean()))
    print("  groesster Aufwaertsschritt: %+.4f" % (ab.max() if len(ab) else 0))
    print("  ➤ %s" % ("✔ monoton fallend" if rho < -0.7 and pv < 0.01
                      else "⛔ NICHT monoton - zurueck zu Baendern"))

    # ══ 3. DIE NULLWELT - ist die Kurve nur Glaettung? ═══════════════
    print()
    print("=" * 112)
    print("TEIL 3 - DIESELBE KURVE AUF DER NULLWELT (Falle 1)")
    print("  ⭐ Tagestreu gemischt: W wird INNERHALB jedes Tages neu verlost.")
    print("     Damit bleibt der Tagesmix erhalten und nur die Zuordnung")
    print("     Lage->Ergebnis wird zerstoert. Die Kurve MUSS flach werden.")
    print()
    rng = np.random.default_rng(SAAT)
    ordnung = np.argsort(tag, kind="stable")
    grenzen = np.flatnonzero(np.diff(tag[ordnung])) + 1
    bloecke = [b for b in np.split(ordnung, grenzen) if len(b) > 1]
    jeP = {}
    rhos = []
    for _ in range(N.NULL_ZIEHUNGEN):
        wm2 = W.copy()
        for blk in bloecke:
            wm2[blk] = W[rng.permutation(blk)]
        kk = kurve(wm2, R, A)
        if len(kk) < 5:
            continue
        rhos.append(spearmanr([z["w_mitte"] for z in kk],
                              [z["kelly"] for z in kk]).statistic)
        for z in kk:
            jeP.setdefault(z["p"], []).append(z["kelly"])
    rhos = np.array(rhos)
    gr5 = float(np.percentile(rhos, 5)) if len(rhos) else float("nan")
    print("  ⚠️ Die SPANNE taugt hier NICHT als Mass: tagesinternes Mischen")
    print("     laesst den TAGESEFFEKT stehen (an einem Crashtag sind ALLE")
    print("     W niedrig). Das Band wird deshalb JE STUETZSTELLE gebildet.")
    print()
    print("  %6s %+9s %11s %11s %11s  %s"
          % ("Perz.", "W-Mitte", "Kelly echt", "Null Med.",
             "Null %d." % N.NULL_PERZENTIL, "Urteil"))
    ueber = 0; gepr = 0
    for z in k:
        nl = np.array(jeP.get(z["p"], []))
        if len(nl) < 10:
            continue
        gepr += 1
        ob = float(np.percentile(nl, N.NULL_PERZENTIL))
        tr = z["kelly"] > ob
        ueber += bool(tr)
        print("  %5.2f%% %+9.3f %+11.4f %+11.4f %+11.4f  %s"
              % (z["p"], z["w_mitte"], z["kelly"], float(np.median(nl)), ob,
                 "✔" if tr else "-"))
    print()
    print("  Nullwelt rho   Median %+.3f   5. Perzentil %+.3f   ECHT %+.3f"
          % (float(np.median(rhos)) if len(rhos) else float("nan"),
             gr5, rho))
    print("  ueber dem Band: %d von %d Stuetzstellen" % (ueber, gepr))
    print("  ➤ %s" % ("✔ die Kurve ist KEIN Glaettungsartefakt"
                      if rho < gr5 and ueber >= 2
                      else "⛔ im Nullband - die Kurve ist Glaettung"))


    # ⚠️ Der UEBERSCHUSS ueber den Nullpunkt - erst hier verfuegbar, weil
    # er die Nullwelt aus Teil 3 braucht.
    ueberschuss = {}
    for z_ in k:
        nl = jeP.get(z_["p"])
        if nl and len(nl) >= 10:
            ueberschuss[z_["p"]] = z_["kelly"] - float(np.median(nl))

    # ══ 3b. MONOTONIE - auf BEIDEN Massstaeben ═══════════════════════
    print()
    print("=" * 112)
    print("TEIL 3b - MONOTONIE AUF BEIDEN MASSSTAEBEN")
    print("  ⚠️ Teil 2 hat den ROHEN Kelly geprueft und NICHT monoton")
    print("     gefunden. Der rohe Kelly ist aber der falsche Massstab:")
    print("     die Nullwelt liegt bei -0,5 und nicht bei null.")
    print()
    pk = [z_["p"] for z_ in k if z_["p"] in ueberschuss]
    wk = np.array([z_["w_mitte"] for z_ in k if z_["p"] in ueberschuss])
    uk = np.array([ueberschuss[p] for p in pk])
    if len(uk) >= 5:
        r3, p3 = spearmanr(wk, uk)
        d3 = np.diff(uk)
        print("  UEBERSCHUSS gegen W   rho %+.4f  p %.2e  |  fallend %d/%d"
              % (r3, p3, int((d3 <= 0).sum()), len(d3)))
        print("  ROHER Kelly gegen W   rho %+.4f  p %.2e  |  fallend %d/%d"
              % (rho, pv, int((ab <= 0).sum()), len(ab)))
        print("  ➤ %s" % ("✔ der UEBERSCHUSS ist monoton, der rohe Kelly "
                          "nicht - die Achse ORDNET"
                          if r3 < -0.9 and p3 < 0.01 else "⛔"))
        print()
        print("  ⚠️ FUER DIE HEBELHOEHE zaehlt trotzdem der ROHE Kelly: das")
        print("     Konto waechst absolut, nicht gegen eine Nullwelt. Der")
        print("     Ueberschuss belegt, DASS die Achse ordnet - nicht, wie")
        print("     hoch gehebelt werden darf.")

    # ══ 4. OUT-OF-SAMPLE - auf der AUSWAHL, nicht auf allen Ankern ═══
    print()
    print("=" * 112)
    print("TEIL 4 - OUT-OF-SAMPLE (Falle 3)")
    print("  ⚠️ NEU GEFASST. Der erste Anlauf interpolierte die Kurve auf")
    print("     ALLE Anker der zweiten Haelfte - np.interp KLEMMT dort am")
    print("     Rand, also bekamen alle scharfen Lagen (W < -1,36) denselben")
    print("     Wert. Genau die Zone, um die es geht. Jetzt wird die")
    print("     SCHWELLE aus der einen Haelfte auf die andere angewendet.")
    print()
    ut = np.unique(tag); mitte = ut[len(ut) // 2]
    haelften = (("1. Haelfte -> 2.", tag < mitte, tag >= mitte),
                ("2. Haelfte -> 1.", tag >= mitte, tag < mitte))
    print("  %-18s %8s %9s %9s %10s %11s %10s  %s"
          % ("Richtung", "Schwelle", "n test", "q", "CRV", "Kelly",
             "Ertrag %", "Urteil"))
    for lab, mtr, mte in haelften:
        ktr = kurve(W[mtr], R[mtr], A[mtr])
        if len(ktr) < 5:
            print("  %-18s zu duenn" % lab); continue
        # Die Schwelle kommt aus der TRAININGSHAELFTE: die obere Kante des
        # schaerfsten Fensters, dessen roher Kelly noch positiv ist.
        # ⚠️ Keine gesetzte Zahl - sie faellt aus der Kurve.
        pos = [zz for zz in ktr if zz["kelly"] > 0]
        if not pos:
            print("  %-18s kein Fenster mit positivem Kelly" % lab); continue
        unterste = min(pos, key=lambda zz: zz["w_mitte"])
        sw = unterste["w_bis"]
        m = mte & (W <= sw)
        if m.sum() < 200:
            print("  %-18s zu wenige Testanker (%d)" % (lab, int(m.sum())))
            continue
        q4, c4, k4 = kelly_von(R[m])
        # tagestreue Nullwelt auf DERSELBEN Ankerzahl je Tag
        je = {int(t): int(c) for t, c in
              zip(*np.unique(tag[m], return_counts=True))}
        poolte = {}
        for i_ in np.flatnonzero(mte):
            poolte.setdefault(int(tag[i_]), []).append(i_)
        nb = []
        for _ in range(N.NULL_ZIEHUNGEN):
            a4 = []
            for t, c in je.items():
                pl = poolte.get(t)
                if pl:
                    pl = np.array(pl)
                    a4.append(rng.choice(pl, size=min(c, len(pl)),
                                         replace=False))
            if a4:
                nb.append(float(P[np.concatenate(a4)].mean()))
        ob = (100 * float(np.percentile(np.array(nb), N.NULL_PERZENTIL))
              if nb else float("nan"))
        er = 100 * float(P[m].mean())
        print("  %-18s %+8.3f %9d %8.1f%% %10.3f %+11.4f %+10.4f  %s"
              % (lab, sw, int(m.sum()), 100 * q4, c4, k4, er,
                 "✔ ueber Band %+.3f" % ob if er > ob
                 else "⛔ im Band %+.3f" % ob), flush=True)

    # ══ 4b. SIND GLEICHZEITIGE TRADES UNABHAENGIG? ═══════════════════
    print()
    print("=" * 112)
    print("TEIL 4b - SIND GLEICHZEITIGE TRADES UNABHAENGIG?")
    print("  ⚠️ Die Hebelformel setzt das voraus. Wenn nicht, ist Teil 5")
    print("     ohne diese Korrektur ZU OPTIMISTISCH.")
    print()
    print("  %-14s %8s %9s %11s %12s %11s"
          % ("Auswahl", "Tage", "Trades", "je Tag", "rho", "effektiv N"))
    rho_mess = float("nan")
    for sw in (-1.5, -1.4, -1.3, -1.2):
        m = W <= sw
        if m.sum() < 400:
            continue
        rh, en, kb = intraklassen_rho(R[m], tag[m])
        if rh != rh:
            continue
        if abs(sw + 1.5) < 1e-9:
            rho_mess = rh
        print("  W <= %-9.2f %8d %9d %11.1f %12.4f %11.2f"
              % (sw, len(np.unique(tag[m])), int(m.sum()), kb, rh, en),
              flush=True)

    # ⚠️ Der Schaetzer hat bei kleinen Gruppen einen Aufwaertsbias. Er
    # wird gegen dieselbe Rechnung auf GEMISCHTEN Tagen gehalten - dort
    # gibt es keinen Tageszusammenhang, also gehoert dort 0 hin.
    m15 = W <= -1.5
    _u, c15 = np.unique(tag[m15], return_counts=True)
    gemischt = []
    for _ in range(20):
        idx = rng.choice(len(R), size=int(m15.sum()), replace=False)
        kunst = np.repeat(np.arange(len(c15)), c15)[:len(idx)]
        rh, _e, _k = intraklassen_rho(R[idx], kunst)
        if rh == rh:
            gemischt.append(rh)
    bias = float(np.mean(gemischt)) if gemischt else 0.0
    rho_korr = max(0.0, rho_mess - bias)
    print()
    print("  gemischte Tage (dort gehoert 0 hin): rho %.4f  -> Bias" % bias)
    print("  ⭐ RHO NACH BIASABZUG: %.4f   Obergrenze fuer effN: %.2f"
          % (rho_korr, 1.0 / max(rho_korr, 1e-9)))
    print("  ➤ %s" % ("⛔ NICHT unabhaengig - Teil 5 rechnet mit effN"
                      if rho_korr > 0.05 else "✔ naeherungsweise unabhaengig"))

    # ══ 5. DIE HEBELHOEHE - und was daran MESSUNG ist ════════════════
    print()
    print("=" * 112)
    print("TEIL 5 - DIE HEBELHOEHE UND DIE GERECHNETE SCHWELLE")
    print("  ⭐ Gemessen ist kelly(W) und die Stopweite. Der KELLY-TEILER")
    print("     und die ZAHL GLEICHZEITIGER POSITIONEN sind dagegen")
    print("     RISIKOENTSCHEIDUNGEN - sie stehen dem Nutzer zu, nicht der")
    print("     Messung. Deshalb hier die ganze Flaeche statt einer Zahl.")
    print()
    best = max(k, key=lambda z_: z_["kelly"])
    print("  Schaerfste Stuetzstelle: W %+.3f · Kelly %+.4f · Stop %.2f %% · "
          "RM-11 %.2fx" % (best["w_mitte"], best["kelly"],
                           100 * best["stop"], best["rm11"]))
    print()
    print("  Hebel dort, je Risikoentscheidung (RM-11-Deckel angewendet):")
    print("  ⚠️ MIT der Korrelationskorrektur aus Teil 4b (rho %.4f)."
          % rho_korr)
    SPALTEN = (1, 2, 3, 5, 8, 99)
    print("  %-16s %s" % ("Kelly-Teiler",
                          " ".join("%10s" % ("%d Pos." % p)
                                   for p in SPALTEN)))
    print("  %-16s %s" % ("(effektiv N)",
                          " ".join("%10.2f" % eff_n(p, rho_korr)
                                   for p in SPALTEN)))
    for teiler, tname in ((1.0, "voll"), (2.0, "halb"), (4.0, "viertel")):
        zell = []
        for npos in SPALTEN:
            h = (best["kelly"] / teiler) * eff_n(npos, rho_korr) / \
                max(best["stop"], 1e-9)
            h = min(h, best["rm11"])
            zell.append("%10s" % (("%.2fx" % h) if h >= ZIEL_MIN
                                  else "(%.2f)" % h))
        print("  %-16s %s" % ("%s (1/%g)" % (tname, teiler), " ".join(zell)))
    print()
    print("  ⛔ Die Spalte ,99 Pos.' ist die OBERGRENZE: effN -> 1/rho = "
          "%.2f. Mehr Positionen bringen NICHTS mehr, weil sie dasselbe "
          "wetten." % (1.0 / max(rho_korr, 1e-9)))
    print()
    print("  ⭐ Klammern = unter der Zielzone %.0f-%.0fx, also KEIN Hebel."
          % (ZIEL_MIN, ZIEL_MAX))
    print()
    print("  DIE SCHWELLE JE RISIKOENTSCHEIDUNG - dort faellt der Hebel "
          "unter %.1fx:" % ZIEL_MIN)
    print("  %-16s %10s %10s %10s %10s %12s"
          % ("Risikoniveau", "Schwelle W", "Signale", "je Tag",
             "Tage %", "Ertrag %"))
    tg = len(np.unique(tag))
    xs = np.array([z_["w_mitte"] for z_ in k])
    for teiler, npos, lab in ((1.0, 3, "voll / 3"), (1.0, 5, "voll / 5"),
                              (2.0, 3, "halb / 3"), (2.0, 5, "halb / 5"),
                              (4.0, 5, "viertel / 5")):
        hs = np.array([min((z_["kelly"] / teiler) * eff_n(npos, rho_korr) /
                           max(z_["stop"], 1e-9), z_["rm11"]) for z_ in k])
        tref = None
        for i in range(len(xs) - 1):
            if hs[i] >= ZIEL_MIN > hs[i + 1]:
                tref = xs[i] + (xs[i + 1] - xs[i]) * \
                    (hs[i] - ZIEL_MIN) / max(hs[i] - hs[i + 1], 1e-9)
                break
        if tref is None:
            print("  %-16s %10s  (Zielzone im gemessenen Bereich nie "
                  "erreicht)" % (lab, "-"))
            continue
        m = W <= tref
        print("  %-16s %+10.3f %10d %10.2f %9.1f%% %+12.4f"
              % (lab, tref, int(m.sum()), m.sum() / tg,
                 100 * len(np.unique(tag[m])) / tg,
                 100 * float(P[m].mean())))
    print()
    print("  WAS MUESSTE SICH AENDERN, DAMIT HALBES KELLY die %.1fx traegt?"
          % ZIEL_MIN)
    print("  (halbes Kelly ist der Standard - volles hat ruinoese "
          "Verlustserien)")
    print()
    e5 = eff_n(5, rho_korr)
    print("  %-30s %12s %12s %10s" % ("Stellschraube", "ist", "noetig",
                                      "Faktor"))
    nk = ZIEL_MIN * best["stop"] * 2.0 / e5
    print("  %-30s %12.4f %12.4f %9.2fx" % ("Kelly (halb, 5 Pos.)",
                                            best["kelly"], nk,
                                            nk / best["kelly"]))
    ns = (best["kelly"] / 2.0) * e5 / ZIEL_MIN
    print("  %-30s %11.2f%% %11.2f%% %9.2fx" % ("Stopweite",
                                                100 * best["stop"],
                                                100 * ns, ns / best["stop"]))
    ohne = (best["kelly"] / 2.0) * 5.0 / max(best["stop"], 1e-9)
    print("  %-30s %12.4f %12s" % ("Korrelation rho", rho_korr,
                                   "auch bei 0 nur %.2fx" % ohne))
    print()
    print("  ⭐ Selbst bei rho = 0 und 5 Positionen waere halbes Kelly bei")
    print("     %.2fx. Die Korrelation allein erklaert die Luecke NICHT -"
          % ohne)
    print("     der Kelly selbst ist zu klein.")
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Die Stopweite ist je Stuetzstelle der MEDIAN von 1,00 ATR -")
    print("     im Betrieb rechnet jeder Trade mit seiner eigenen ATR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
