# -*- coding: utf-8 -*-
"""Die NEUDIMENSIONIERUNG des Hebels - Horizont, Stop, Trailing, Hebelhoehe

**26.09.2026**, Nutzerauftrag: *"der Hebel wird neu dimensioniert und auch
neu vermessen, da dies bereits der dritte grosse Hebelumbau ist"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_22_Neudimensionierung_26_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM DIESE MESSUNG
═══════════════════════════════════════════════════════════════════════

Die BEWERTUNG steht (2.608). Was nicht steht, sind die Groessen, die aus
einem Signal einen TRADE machen - und sie stammen aus vier Quellen mit vier
Annahmen. Die Haltedauer zum Beispiel:

    1,1 Tage     Bitpanda-Trades des Nutzers (kalibriert den 15-Min-Takt)
    0,30 Tage    Median derselben Trades (2.493)
    3,4 Tage     Rechenannahme der Kette (2.513)
    72 h         meine eigene Setzung (2.607)

⚠️ KEINE davon beschreibt Systemtrades, und im Signal steht `holding_
duration = NULL` bei allen 22. Die Haltedauer ist eine ENTSCHEIDUNG, die
aus der Messung fallen muss.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DIE DREI FALLEN
═══════════════════════════════════════════════════════════════════════

    ⚠️ FALLE 1   `R` IST KEINE FESTE EINHEIT. Aendert sich die Stopweite,
                 aendert sich R - `E[R]` ueber Stopweiten zu vergleichen
                 misst den MASSSTAB, nicht die Leistung (derselbe Fehler
                 in 2.607 und 2.616).
                 ➤ Jede Zelle in BEIDEN Einheiten. Nur KURSPROZENT
                   entscheidet zwischen Stopweiten.

    ⚠️ FALLE 2   DIE AUSWAHLHAERTE MUSS GLEICH SEIN. Die Schwelle 1,0 ATR
                 waehlt je Horizont eine andere Zahl Anker.
                 ➤ Der AUSWAHLANTEIL wird angeglichen, nicht die Schwelle.

    ⚠️ FALLE 3   DER GEOMETRISCHE ERTRAG IST NICHT DER ARITHMETISCHE. Bei
                 schiefer Verteilung (2.609: Median -0,1885) liegt er
                 darunter - und genau er bestimmt, was ein Konto tut.
                 ➤ Die HEBELHOEHE folgt dem geometrischen, nicht E[R].

═══════════════════════════════════════════════════════════════════════
 GESTAFFELT, NICHT ALS VOLLES GITTER
═══════════════════════════════════════════════════════════════════════

6 x 5 x 4 x 3 = 360 Zellen auf 3,18 Mio Ankern sind nicht rechenbar.

    Stufe G   Horizont x Stopweite          30 Zellen   bestimmen R
    Stufe T   Ausloeser x Abstand           12 Zellen   brauchen stabiles R

⭐ DIESELBE Ankermenge fuer beide - die Staffelung betrifft die Auswertung,
nicht die Grundgesamtheit. ⚠️ Eine Wechselwirkung zwischen Stopweite und
Ausloeser saehe sie nicht; deshalb laeuft Stufe T ZUSAETZLICH auf der
zweitbesten Geometrie.

⚠️ NUR LESEN.  python messe_hebel_neudimension.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema, trailing            # noqa: E402

EMA_L = 48                          # aus 2.606
VORLAUF = 240
SCHWELLE = 1.0                      # aus 2.608
# ⚠️⚠️ NACH UNTEN ERWEITERT (26.09., gerechnet): die Finanzierung
# kostet 0,18 %/Tag (2.556). Gegen den Ertrag von +0,6611 % aus 2.616
# bleibt bei 3 Tagen nur +0,1211 % (82 % weg), bei 5 Tagen ist er
# NEGATIV. Die urspruengliche Achse 6-120 h war zu hoch angesetzt.
# ⭐ Der Nutzer-Median von 0,30 Tagen (7,2 h) liegt im guenstigen Bereich.
HORIZONTE = (2, 3, 6, 12, 24, 48, 72)
STOPWEITEN = (1.0, 1.5, 2.0, 2.5, 3.0)
AUSLOESER = (0.0, 0.5, 1.0, 1.5)
ABSTAENDE = (0.5, 1.0, 1.5)
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND = 300
SAAT = 20260926


# ═══════════════════════════════════════════════════════════════════════
#  Der Trailing-Rechner mit AUSLOESER - die Verallgemeinerung von 2.607
# ═══════════════════════════════════════════════════════════════════════

def trailing_mit_ausloeser(high, low, close, atr, weite, ausloese_r,
                           abstand_r, H):
    """-> (r, kursprozent) je Anker.

    ⭐⭐ P1 - DIE SELBSTPROBE STECKT IM BAU: bei `ausloese_r = 0` und
    `abstand_r == weite` ist das genau die Regel aus 2.607 (Stop von
    Anfang an `weite x ATR` unter dem Hoechstkurs). `main` weist die
    Bitgleichheit gegen `trailing()` nach.

    ⚠️ Der ERSTE Stop liegt immer bei `weite x ATR` unter dem Einstieg -
    das ist das Anfangsrisiko und der Nenner von R. Der Ausloeser sagt
    nur, ab welchem MFE nachgezogen wird.
    """
    n = len(close)
    idx = np.arange(n)
    risiko = np.maximum(weite * atr * close, 1e-12)
    stop = close - risiko
    hoechst = close.copy()
    fertig = np.zeros(n, bool)
    ausstieg = np.full(n, np.nan)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        offen = ~fertig
        raus = offen & (low[j] <= stop)
        ausstieg[raus] = stop[raus]
        fertig |= raus
        neu = ~fertig
        hoechst = np.where(neu & (high[j] > hoechst), high[j], hoechst)
        # ⭐ DER AUSLOESER: nachgezogen wird erst, wenn das MFE in R die
        # Schwelle erreicht hat. Bei ausloese_r = 0 ist das immer wahr.
        mfe_r = (hoechst - close) / risiko
        zieht = neu & (mfe_r >= ausloese_r)
        neuer = hoechst - abstand_r * risiko
        stop = np.where(zieht, np.maximum(stop, neuer), stop)
    je = np.minimum(idx + H, n - 1)
    ausstieg = np.where(np.isnan(ausstieg), close[je], ausstieg)
    r = (ausstieg - close) / risiko
    return r, (ausstieg - close) / np.maximum(close, 1e-12)


def laengste_verlustserie(werte):
    """Die laengste ununterbrochene Folge negativer Ergebnisse.

    ⚠️ Sie ist die eigentliche Hebelgrenze: nicht der Erwartungswert
    begrenzt den Hebel, sondern die laengste Durststrecke, die ein Konto
    ueberleben muss.
    """
    lauf = best = 0
    for w in werte:
        if w < 0:
            lauf += 1
            best = max(best, lauf)
        else:
            lauf = 0
    return best


def geometrisch(r, einsatz=0.01):
    """Geometrischer Ertrag je Trade bei `einsatz` Kontoanteil Risiko.

    ⚠️⚠️ FALLE 3: bei schiefer Verteilung liegt er UNTER dem
    arithmetischen Mittel, und er ist es, der bestimmt, was ein Konto
    ueber viele Trades tut. `einsatz` ist der Anteil des Kontos, der bei
    -1 R verloren geht (RM-1: 1 Prozent beim Hebel).
    """
    x = 1.0 + einsatz * np.asarray(r, float)
    if np.any(x <= 0):
        return float("-inf")            # Totalverlust moeglich
    return float(np.expm1(np.mean(np.log(x))))


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 108)
    print("DIE NEUDIMENSIONIERUNG DES HEBELS")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  Schwelle %.1f ATR (2.608) · EMA %d h (2.606)"
          % (SCHWELLE, EMA_L))
    print("  Stufe G: %d Horizonte x %d Stopweiten = %d Zellen"
          % (len(HORIZONTE), len(STOPWEITEN),
             len(HORIZONTE) * len(STOPWEITEN)))
    print("  Stufe T: %d Ausloeser x %d Abstaende = %d Zellen"
          % (len(AUSLOESER), len(ABSTAENDE),
             len(AUSLOESER) * len(ABSTAENDE)))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    Hmax = max(HORIZONTE)
    print("  %d Symbole · %d Stunden · Hmax %d h"
          % (len(kurse), len(sl), Hmax), flush=True)

    # ── Vorbereitung je Symbol: Merkmal und Gueltigkeit ───────────────
    # ⚠️ P3: ein Anker zaehlt nur, wenn er fuer den LAENGSTEN Horizont
    # auswertbar ist - sonst haette jede Zelle ihre eigene Menge.
    daten = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - Hmax):] = False
        sel = np.flatnonzero(gu)
        if len(sel):
            daten.append((np.array([sid[x] for x in st], np.int64),
                          h, l, cc, atr, w, sel))
    G = np.concatenate([d[0][d[6]] for d in daten])
    W = np.concatenate([d[5][d[6]] for d in daten])
    n = len(G)
    ntage = len(np.unique(G // 24))
    print("  %d Anker (fuer Hmax gueltig, P3) · %d Tage" % (n, ntage),
          flush=True)

    rng = np.random.default_rng(SAAT)

    def rechne(hz, weite, ausl, abst):
        """-> (r, prozent) ueber die gemeinsame Ankermenge."""
        rr, pp = [], []
        for idx, h, l, cc, atr, w, sel in daten:
            a, b = trailing_mit_ausloeser(h, l, cc, atr, weite, ausl,
                                          abst, hz)
            rr.append(a[sel]); pp.append(b[sel])
        return np.concatenate(rr), np.concatenate(pp)

    # ══ P1: der Grenzfall muss 2.607 bitgleich reproduzieren ═════════
    print()
    d0 = daten[0]
    a1, _ = trailing_mit_ausloeser(d0[1], d0[2], d0[3], d0[4], 1.0, 0.0,
                                   1.0, 72)
    a2 = trailing(d0[1], d0[2], d0[3], d0[4], 1.0, 72)
    ok = bool(np.allclose(np.nan_to_num(a1), np.nan_to_num(a2),
                          rtol=0, atol=0))
    print("  P1  Grenzfall (ausloese=0, abstand=weite) bitgleich mit "
          "trailing(): %s" % ("✔ JA" if ok else "⛔ NEIN - ABBRUCH"))
    if not ok:
        d = np.abs(np.nan_to_num(a1) - np.nan_to_num(a2))
        print("      groesste Abweichung %.3e an %d Stellen"
              % (d.max(), int((d > 0).sum())))
        return 1

    # ══ STUFE G: Horizont x Stopweite ════════════════════════════════
    print()
    print("=" * 108)
    print("STUFE G - HORIZONT x STOPWEITE (Trailing wie 2.607: "
          "ausloese 0, abstand = weite)")
    print("  ⚠️ FALLE 1: nur KURSPROZENT vergleicht ueber Stopweiten "
          "hinweg - E[R] misst den Massstab mit")
    print()
    print("  %-5s %-6s %8s %8s %9s %10s %9s %9s %8s %7s  %s"
          % ("H", "Stop", "Signale", "Sig/Tag", "E[R]", "Kurs %",
             "Median %", "geom %", "Treffer", "Serie", "Urteil"))
    # Referenzzelle gibt den Auswahlanteil vor (FALLE 2)
    k_soll = int((np.isfinite(W) & (W >= SCHWELLE)).sum())
    print("  (Auswahlanteil fest: %d Anker = %.1f %% - aus H72/Stop2,0)"
          % (k_soll, 100.0 * k_soll / n))
    print()
    pos_alle = np.flatnonzero(np.isfinite(W))
    ordn = pos_alle[np.argsort(W[pos_alle])[::-1][:k_soll]]
    zellen = []
    nullproben = []
    for hz in HORIZONTE:
        for weite in STOPWEITEN:
            r, p = rechne(hz, weite, 0.0, weite)
            rs, ps = r[ordn], p[ordn]
            nb = [float(p[rng.choice(n, size=k_soll, replace=False)].mean())
                  for _ in range(N_NULL)]
            nullproben.append(nb)
            b90 = float(np.percentile(np.array(nb), NULL_PERZ)) * 100
            pz = 100 * float(ps.mean())
            ge = 100 * geometrisch(rs)
            tr = float((rs > 0).mean())
            serie = laengste_verlustserie(rs[np.argsort(G[ordn])])
            zellen.append(dict(h=hz, weite=weite, er=float(rs.mean()),
                               pz=pz, ge=ge, tr=tr, serie=serie, b90=b90,
                               med=100 * float(np.median(ps))))
            print("  %-5d %-6.1f %8d %8.2f %+9.4f %+10.4f %+9.4f %+9.5f "
                  "%7.1f%% %7d  %s"
                  % (hz, weite, k_soll, k_soll / max(ntage, 1),
                     float(rs.mean()), pz, 100 * float(np.median(ps)), ge,
                     100 * tr, serie,
                     "✔" if pz > b90 else "⛔ im Band"), flush=True)

    # ══ P5: das Mehrfachtesten ═══════════════════════════════════════
    best = max(zellen, key=lambda z: z["pz"])
    arr = np.array(nullproben) * 100          # (Zellen, Ziehungen)
    bestes_je_ziehung = arr.max(axis=0)
    b90_mehr = float(np.percentile(bestes_je_ziehung, NULL_PERZ))
    print()
    print("  P5  MEHRFACHTESTEN ueber %d Zellen" % len(zellen))
    print("      Einzelband %.4f %% · ⭐ BESTES-VON-%d-Band %.4f %%"
          % (float(np.percentile(arr[0], NULL_PERZ)), len(zellen), b90_mehr))
    print("      beste Zelle: H%d / Stop %.1f mit %+.4f %%  -> %s"
          % (best["h"], best["weite"], best["pz"],
             "✔✔ auch gegen das Mehrfachtesten"
             if best["pz"] > b90_mehr else
             "⛔ NICHT gegen das Mehrfachtesten - das ist Auslese"))

    # Robustheit: wie flach ist die Umgebung?
    print()
    print("  ROBUSTHEIT - die drei besten Zellen")
    for z in sorted(zellen, key=lambda x: -x["pz"])[:3]:
        print("      H%-4d Stop %.1f  Kurs %+7.4f %%  geom %+8.5f %%  "
              "Treffer %.1f %%  Serie %d"
              % (z["h"], z["weite"], z["pz"], z["ge"], 100 * z["tr"],
                 z["serie"]))
    print()
    print("  ⚠️ Gewaehlt wird die ROBUSTESTE, nicht die hoechste - eine")
    print("     Zelle mit flacher Umgebung haelt, eine Spitze nicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
