# -*- coding: utf-8 -*-
"""Was macht die Sperre aus 2.601 mit `E[R]_alle`?

**26.09.2026**, Nutzerauftrag: *"ja rechnen - pruefen und gegenpruefen"*.

Befund 2.601 hat eine belegte SPERRE gefunden: *BTC steigt UND Dominanz
steigt* liegt bei **-0,0134 ± 0,0077** (tagesgeblockt) und ist damit vom
Null verschieden. Die Frage ist jetzt, was ihr Wegsperren bringt.

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE UND IHRE FALLE
═══════════════════════════════════════════════════════════════════════

    Hebt die Sperre `E[R]_alle` - und wenn ja, um wieviel?

⚠️⚠️⚠️ **Die Falle ist die Rueckschau.** Die Sperre wurde AUF DENSELBEN
DATEN gefunden, auf denen sie jetzt wirken soll. Die schlechteste Zelle
eines Rasters wegzulassen verbessert den Rest IMMER - auch wenn das Raster
reiner Zufall ist. Eine Rechnung ohne Gegenprobe waere deshalb wertlos.

═══════════════════════════════════════════════════════════════════════
 DIE VIER PRUEFUNGEN
═══════════════════════════════════════════════════════════════════════

    P1  SELBSTPROBE   die arithmetische Vorhersage und die gemessene Zahl
                      muessen uebereinstimmen. Sonst rechnet das Werkzeug
                      etwas anderes, als es behauptet.

    P2  ⭐ NULLWELT DER UEBERANPASSUNG
                      Wieviel Verbesserung entsteht ALLEIN dadurch, dass
                      man die schlechteste Zelle eines Rasters sucht? Dazu
                      wird dieselbe Prozedur auf ZUFALLSachsen angewandt:
                      Raster bilden, schlechteste Zelle sperren, Gewinn
                      messen. 40 Ziehungen.
                      ⚠️ Eine zufaellige Sperre GLEICHER GROESSE waere die
                      falsche Nullwelt - sie enthaelt die Suche nicht.

    P3  ⭐⭐ OUT-OF-SAMPLE (B6)
                      Die Sperre wird auf der ERSTEN Haelfte bestimmt und
                      auf der ZWEITEN angewandt. Nur dieser Gewinn ist
                      echt; der In-Sample-Gewinn ist eine Obergrenze.

    P4  SCHWELLEN-SENSITIVITAET
                      Die Schwellen (BTC > +0,5 %, Dominanz > 0) stammen aus
                      derselben Messung. Haelt der Gewinn auch daneben?
                      Ein Effekt, der nur bei EINER Schwelle auftritt, ist
                      eine Anpassung an das Raster.

⚠️ NUR LESEN.

    python messe_sperre_wirkung.py [--symbole N]
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX)

LEITWERT = os.path.join("data", "btc_leitwert.db")
K_ATR = 1.0
ZELLEN = ((1.5, 6), (1.5, 24))
RUECK_H = 6
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
SAAT = 20260926
#: die Sperre aus 2.601 und ihre Nachbarn - fuer P4
SCHWELLEN = ((0.0025, 0.0), (0.005, 0.0), (0.010, 0.0), (0.005, 0.0025))


def _rendite(x, h):
    r = np.full(len(x), np.nan)
    if len(x) > h:
        with np.errstate(invalid="ignore", divide="ignore"):
            r[h:] = x[h:] / np.maximum(x[:-h], 1e-12) - 1.0
    return r


def _tagesfehler(r, tage):
    """Streuung ueber TAGE, nicht ueber Anker - wegen der Clusterung."""
    ut = np.unique(tage)
    if len(ut) < 30:
        return float("nan")
    pos = np.searchsorted(ut, tage)
    sm = np.bincount(pos, weights=r, minlength=len(ut))
    cn = np.bincount(pos, minlength=len(ut)).astype(float)
    je = sm / np.maximum(cn, 1)
    return float(np.std(je, ddof=1) / np.sqrt(len(ut)))


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("WAS BRINGT DIE SPERRE AUS 2.601?")
    print("=" * 100)
    print("  Sperre: BTC steigt (>+0,5 %% / 6 h) UND Dominanz steigt")
    print("  ⚠️ Die Falle ist die RUECKSCHAU: die schlechteste Zelle eines")
    print("     Rasters wegzulassen verbessert den Rest IMMER - auch bei")
    print("     reinem Zufall. Deshalb P2 (Nullwelt) und P3 (out-of-sample).")

    kurse = lade_kurse(grenze)
    alle = set()
    for (stunden, *_r) in kurse.values():
        alle.update(stunden)
    stundenliste = sorted(alle)
    sid = {s: i for i, s in enumerate(stundenliste)}
    T = len(stundenliste)

    c = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    reihen = c.execute("SELECT stunde, close FROM leitwert WHERE symbol='BTC' "
                       "ORDER BY stunde").fetchall()
    c.close()
    btc = np.full(T, np.nan)
    for st, cl in reihen:
        i = sid.get(st)
        if i is not None:
            btc[i] = cl
    btc_r = _rendite(btc, RUECK_H)

    alt_s, alt_n = np.zeros(T), np.zeros(T)
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        if sym.upper() == "BTC":
            continue
        ii = np.array([sid[x] for x in stunden], np.int64)
        rr = _rendite(close, RUECK_H)
        g = np.isfinite(rr)
        np.add.at(alt_s, ii[g], rr[g]); np.add.at(alt_n, ii[g], 1.0)
    with np.errstate(invalid="ignore"):
        alt_m = np.where(alt_n >= 5, alt_s / np.maximum(alt_n, 1), np.nan)
    dom = btc_r - alt_m
    print("  %d Symbole · %d Stunden · Dominanz-Proxy %d Stunden belegt"
          % (len(kurse), T, int(np.isfinite(dom).sum())), flush=True)

    rng = np.random.default_rng(SAAT)
    for crv, H in ZELLEN:
        IDX, R = [], []
        for sym, (stunden, high, low, close, volumen) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[s] for s in stunden], np.int64)
            atr = atr_tag_relativ(high, low, close)
            stop = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
            zz, ss, ro, gu, _g = ausgaenge(high, low, close, stop,
                                           crv * stop, H)
            gu = gu & np.isfinite(btc_r[idx]) & np.isfinite(dom[idx])
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            IDX.append(idx[sel])
            R.append(np.where(zz[sel], crv,
                              np.where(ss[sel], -1.0,
                                       np.nan_to_num(ro[sel]))))
        if not IDX:
            continue
        IDX = np.concatenate(IDX); R = np.concatenate(R)
        tage = IDX // 24
        b, d = btc_r[IDX], dom[IDX]
        n = len(R)
        er_alle = float(R.mean())
        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · E[R]_alle %+.5f (Fehler ±%.5f)"
              % (crv, H, n, er_alle, _tagesfehler(R, tage)))

        # ── P1 SELBSTPROBE ────────────────────────────────────────────
        sperre = (b > 0.005) & (d > 0.0)
        ns = int(sperre.sum())
        er_sp = float(R[sperre].mean()) if ns else float("nan")
        er_rest = float(R[~sperre].mean())
        # arithmetisch vorhergesagt
        vorher = (er_alle * n - er_sp * ns) / max(n - ns, 1)
        print("  P1 SELBSTPROBE  gesperrt %d Anker (%.1f %%) mit E[R] %+.5f"
              % (ns, 100.0 * ns / n, er_sp))
        print("      Rest gemessen %+.5f · arithmetisch %+.5f · %s"
              % (er_rest, vorher,
                 "✔ stimmt ueberein" if abs(er_rest - vorher) < 1e-9
                 else "⛔ ABWEICHUNG %.2e" % abs(er_rest - vorher)))
        print("      ➤ GEWINN %+.5f (von %+.5f auf %+.5f) · Rest %s"
              % (er_rest - er_alle, er_alle, er_rest,
                 "UEBER NULL ⭐⭐" if er_rest > 0 else "weiter unter null"))

        # ── P2 NULLWELT DER UEBERANPASSUNG ────────────────────────────
        #
        # ⭐ Dieselbe PROZEDUR auf Zufallsachsen: Raster bilden,
        # schlechteste Zelle sperren, Gewinn messen. Das misst genau den
        # Anteil, der allein aus dem SUCHEN entsteht.
        gewinne = []
        for _ in range(N_NULL):
            za, zb = rng.random(n), rng.random(n)
            # gleiches Raster wie oben: 2 x 2, Schwellen auf den Quantilen
            # die dieselbe Zellgroesse ergeben
            qa = np.quantile(za, 1.0 - (b > 0.005).mean())
            qb = np.quantile(zb, 1.0 - (d > 0.0).mean())
            beste = None
            for ma in ((za > qa), ~(za > qa)):
                for mb in ((zb > qb), ~(zb > qb)):
                    m = ma & mb
                    if m.sum() < 1000 or (~m).sum() < 1000:
                        continue
                    w = float(R[m].mean())
                    if beste is None or w < beste[0]:
                        beste = (w, m)
            if beste is None:
                continue
            gewinne.append(float(R[~beste[1]].mean()) - er_alle)
        if gewinne:
            g = np.array(gewinne)
            gr = float(np.percentile(g, NULL_PERZ))
            echt = er_rest - er_alle
            print("  P2 NULLWELT     Suche-nach-der-schlechtesten-Zelle auf "
                  "ZUFALLSachsen")
            print("      %d Ziehungen · Nullpunkt %+.5f · %d. Perz %+.5f · "
                  "gemessen %+.5f"
                  % (len(g), float(g.mean()), int(NULL_PERZ), gr, echt))
            print("      ➤ %s"
                  % ("✔✔ der Gewinn ist GROESSER als die blosse Suche"
                     if echt > gr else
                     "⛔ IM NULLBAND - der Gewinn ist nur die Suche selbst"))

        # ── P3 OUT-OF-SAMPLE (B6) ─────────────────────────────────────
        mitte = int(np.median(tage))
        h1, h2 = tage <= mitte, tage > mitte
        if h1.sum() > 1000 and h2.sum() > 1000:
            # Schwelle auf H1 bestimmen: welche der vier Zellen ist dort
            # die schlechteste?
            beste = None
            for ma, na in ((b > 0.005, "BTC steigt"), (b <= 0.005, "BTC nicht")):
                for mb, nb in ((d > 0.0, "Dom steigt"), (d <= 0.0, "Dom faellt")):
                    m = ma & mb & h1
                    if m.sum() < 1000:
                        continue
                    w = float(R[m].mean())
                    if beste is None or w < beste[0]:
                        beste = (w, ma & mb, "%s + %s" % (na, nb))
            if beste is not None:
                _w, maske, etikett = beste
                a2 = float(R[h2].mean())
                b2 = float(R[h2 & ~maske].mean())
                print("  P3 OUT-OF-SAMPLE (B6)")
                print("      auf Haelfte 1 schlechteste Zelle: %s" % etikett)
                print("      Haelfte 2: %+.5f -> %+.5f · GEWINN %+.5f · "
                      "Fehler ±%.5f"
                      % (a2, b2, b2 - a2,
                         _tagesfehler(R[h2 & ~maske], tage[h2 & ~maske])))
                print("      ➤ %s"
                      % ("✔ dieselbe Zelle wie in-sample"
                         if etikett.startswith("BTC steigt + Dom steigt")
                         else "⚠️ ANDERE Zelle als in-sample - die Sperre "
                              "ist nicht stabil"))

        # ── P4 SCHWELLEN-SENSITIVITAET ────────────────────────────────
        print("  P4 SCHWELLEN    (BTC-Grenze, Dominanz-Grenze) -> Gewinn")
        for sb, sd in SCHWELLEN:
            m = (b > sb) & (d > sd)
            if m.sum() < 1000:
                continue
            print("      (%.4f, %.4f)  gesperrt %5.1f %% · E[R] der Zelle "
                  "%+.5f · Gewinn %+.5f"
                  % (sb, sd, 100.0 * m.sum() / n, float(R[m].mean()),
                     float(R[~m].mean()) - er_alle))
    print()
    print("  ⚠️ Ein Gewinn zaehlt nur, wenn P2 UND P3 ihn bestaetigen.")
    print("     P1 allein ist Arithmetik, keine Aussage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
