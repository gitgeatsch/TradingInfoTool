# -*- coding: utf-8 -*-
"""Woher kommt die negative DRIFT? - Schritt 2 des Hebel-Neubaus

**Nutzerentscheidung 25.09.2026:** Drift zerlegen, bevor die A-Faktoren
gebaut werden.

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE
═══════════════════════════════════════════════════════════════════════

Befund 2.597 hat gemessen: `E[R]` BRUTTO ist in **0 von 60 Zellen** positiv,
bester Wert -0,0034. Ursache ist die DRIFT - sie ist in jedem Fuenftel und
jeder Zelle negativ (-0,0014 bis -0,0210).

Dafuer gibt es zwei sehr verschiedene Erklaerungen, und sie fuehren zu
entgegengesetzten Schluessen:

    (A) MARKTFENSTER    2021-12 bis 2026-09 war im Mittel fallend.
                        ➤ Dann traegt Long in anderen Jahren, und der
                          Hebel ist eine Regimefrage.

    (B) TEILMENGE       Einige Symbole laufen gegen null und ziehen das
                        Mittel mit.
                        ➤ Dann ist es eine HANDELBARKEITSfrage, keine
                          Lagefrage - und die Loesung liegt in der
                          Grundgesamtheit, nicht in der Bewertung.

⚠️ Die beiden schliessen sich nicht aus. Gemessen wird, WIEVIEL jede traegt.

═══════════════════════════════════════════════════════════════════════
 DIE DREI ACHSEN
═══════════════════════════════════════════════════════════════════════

    JAHR              2022 ... 2026 (2021 ist nur ein Monat)
    VOLUMEN-FUENFTEL  30-Tage-Mittel bis t, also STRENG KAUSAL. Das ist
                      die Liquiditaetsachse und damit die Handelbarkeit.
    KONZENTRATION     Drift je Symbol: tragen wenige Symbole die Drift
                      oder alle? Median ueber Symbole gegen Mittelwert
                      ueber Anker - eine grosse Differenz IST Konzentration.

⚠️⚠️ **Und die Auswahlfrage in ZWEI Fassungen**, weil nur eine davon
etwas ueber den Betrieb sagt:

    RUECKSCHAU   die schlechtesten Symbole nach der Drift des GESAMTEN
                 Fensters weglassen. ⛔ Das ist KEINE Strategie - es
                 waehlt nach dem Ergebnis. Es beantwortet nur die
                 Diagnosefrage *wie stark konzentriert ist die Drift*.
    KAUSAL       die schlechtesten Symbole nach der Drift des VORJAHRES
                 weglassen. ✔ Das ist eine echte Betriebsregel, und nur
                 diese Zahl darf in eine Bewertung.

➤ **Die Differenz der beiden ist die Auskunft**: ist die schlechte Drift
eines Symbols von Jahr zu Jahr VORHERSAGBAR? Faellt die kausale Fassung auf
den Gesamtwert zurueck, ist sie es nicht.

═══════════════════════════════════════════════════════════════════════
 ABNAHMEPROBE
═══════════════════════════════════════════════════════════════════════

    Die ankergewichtete Summe der Teilmengen muss die GESAMTZAHL
    reproduzieren. Eine Zerlegung, die sich nicht zusammensetzt, hat
    eine andere Menge gemessen (R-R11 nach innen).

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_drift_herkunft.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX, VORLAUF)

K_ATR = 1.0                     # der lageneutrale Arm aus 2.597
ZELLEN = ((1.5, 6), (1.5, 24), (2.0, 6), (2.0, 24))
WEGLASS = (0.0, 0.10, 0.20, 0.30)
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
SAAT = 20260925


def volumen_mittel(volumen, stunden_je_tag=24, tage=30):
    """30-Tage-Mittel des Volumens bis t - STRENG KAUSAL.

    ⚠️ Der Wert zur Stunde t nutzt nur Stunden <= t. Ein Volumenmass, das
    in die Zukunft sieht, waere als Liquiditaetsachse wertlos: es wuerde
    genau die Symbole hochstufen, die spaeter gehandelt wurden.
    """
    n = len(volumen)
    fenster = stunden_je_tag * tage
    k = np.ones(fenster) / float(fenster)
    m = np.convolve(np.nan_to_num(volumen), k, mode="full")[:n]
    m[:fenster] = np.nan
    return m


def _jahr(stunden):
    """-> Jahreszahl je Anker. `stunden` sind ISO-Texte oder Zeitstempel."""
    aus = np.empty(len(stunden), np.int16)
    for i, s in enumerate(stunden):
        aus[i] = int(str(s)[:4])
    return aus


def kennzahl(Z, S, RO, crv):
    """-> (E[R] brutto, Drift, Aufloesung) auf der uebergebenen Menge."""
    if not len(Z):
        return np.nan, np.nan, np.nan
    r = np.where(Z, crv, np.where(S, -1.0, np.nan_to_num(RO)))
    return float(r.mean()), float(np.mean(RO)), float((Z | S).mean())


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("WOHER KOMMT DIE NEGATIVE DRIFT? - Schritt 2 des Hebel-Neubaus")
    print("=" * 100)
    print("  Geometrie fest: k = %.2f x ATR (der lageneutrale Arm aus 2.597)"
          % K_ATR)
    print("  ⚠️ Die Frage ist MARKTFENSTER gegen TEILMENGE - und wieviel")
    print("     jede von beiden traegt.")

    kurse = lade_kurse(grenze)
    print("  %d Symbole geladen" % len(kurse), flush=True)

    # ── einmal aufbereiten ────────────────────────────────────────────
    roh = []
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        atr = atr_tag_relativ(high, low, close)
        roh.append((sym, _jahr(stunden), high, low, close, atr,
                    volumen_mittel(volumen)))

    for crv, H in ZELLEN:
        SYM, JAHR, Z, S, RO, VOL = [], [], [], [], [], []
        for (sym, jahr, high, low, close, atr, vm) in roh:
            stop_rel = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
            zz, ss, ro, gu, _gl = ausgaenge(high, low, close, stop_rel,
                                            crv * stop_rel, H)
            sel = np.flatnonzero(gu & np.isfinite(vm))
            if not len(sel):
                continue
            SYM.append(np.full(len(sel), sym, object))
            JAHR.append(jahr[sel]); Z.append(zz[sel]); S.append(ss[sel])
            RO.append(ro[sel]); VOL.append(vm[sel])
        if not SYM:
            continue
        SYM = np.concatenate(SYM); JAHR = np.concatenate(JAHR)
        Z = np.concatenate(Z); S = np.concatenate(S)
        RO = np.concatenate(RO); VOL = np.concatenate(VOL)

        er_g, dr_g, auf_g = kennzahl(Z, S, RO, crv)
        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · GESAMT: E[R] %+.5f · Drift %+.5f "
              "· Aufloesung %.1f %%"
              % (crv, H, len(Z), er_g, dr_g, 100 * auf_g))

        # ── ACHSE 1: JAHR ────────────────────────────────────────────
        print("-" * 100)
        print("  ACHSE 1  JAHR - ist es ein MARKTFENSTER?")
        print("     Jahr    Anker      Drift     E[R] brutto   %s"
              % "E[R] > 0 ?")
        summe, gewicht = 0.0, 0
        drin = np.zeros(len(JAHR), bool)
        for j in sorted(set(JAHR.tolist())):
            m = JAHR == j
            if m.sum() < 5000:
                print("     %4d  %8d   (zu duenn, uebersprungen)" % (j, m.sum()))
                continue
            er, dr, _ = kennzahl(Z[m], S[m], RO[m], crv)
            summe += er * m.sum(); gewicht += m.sum()
            drin |= m
            print("     %4d  %8d   %+.5f     %+.5f      %s"
                  % (j, m.sum(), dr, er,
                     "⭐⭐ JA" if er > 0 else "-"))
        # ── ABNAHMEPROBE: setzt sich die Zerlegung zusammen? ─────────
        #
        # ⚠️ Verglichen wird gegen die Gesamtzahl auf DERSELBEN Menge, also
        # ohne die uebersprungenen Jahre. Die erste Fassung verglich gegen
        # das Gesamt UEBER ALLE Anker und meldete deshalb eine Abweichung
        # von -0,000015, die keine war: sie bestand genau aus den Ankern,
        # die die Zerlegung gar nicht enthielt. Eine Abnahmeprobe, die
        # zwei verschiedene Mengen vergleicht, prueft nichts.
        if gewicht:
            rekon = summe / gewicht
            er_drin, _, _ = kennzahl(Z[drin], S[drin], RO[drin], crv)
            print("     ➤ Abnahmeprobe: gewichtete Summe %+.7f gegen "
                  "dieselbe Menge %+.7f   %s"
                  % (rekon, er_drin,
                     "✔ setzt sich zusammen"
                     if abs(rekon - er_drin) < 1e-9
                     else "⚠️ ABWEICHUNG %+.9f" % (rekon - er_drin)))
            if drin.sum() != len(drin):
                print("        (%d von %d Ankern einbezogen; die uebrigen "
                      "liegen in uebersprungenen Jahren)"
                      % (drin.sum(), len(drin)))

        # ── ACHSE 2: VOLUMEN (kausal) ────────────────────────────────
        print("-" * 100)
        print("  ACHSE 2  VOLUMEN-Fuenftel (30-Tage-Mittel bis t, KAUSAL) - "
              "ist es die HANDELBARKEIT?")
        gr = np.nanpercentile(VOL, [20, 40, 60, 80])
        fv = np.searchsorted(gr, VOL, side="right")
        print("     Fuenftel  Anker      Drift     E[R] brutto   %s"
              % "E[R] > 0 ?")
        for q in range(5):
            m = fv == q
            if m.sum() < 5000:
                continue
            er, dr, _ = kennzahl(Z[m], S[m], RO[m], crv)
            print("       %d     %8d   %+.5f     %+.5f      %s"
                  % (q, m.sum(), dr, er, "⭐⭐ JA" if er > 0 else "-"))

        # ── ACHSE 3: KONZENTRATION ───────────────────────────────────
        print("-" * 100)
        print("  ACHSE 3  KONZENTRATION - tragen WENIGE Symbole die Drift?")
        syms = sorted(set(SYM.tolist()))
        dr_je = {}
        for sy in syms:
            m = SYM == sy
            if m.sum() < 500:
                continue
            dr_je[sy] = float(np.mean(RO[m]))
        if dr_je:
            werte = np.array(list(dr_je.values()))
            print("     %d Symbole · Drift-MEDIAN ueber Symbole %+.5f · "
                  "Mittelwert ueber Anker %+.5f"
                  % (len(werte), float(np.median(werte)), dr_g))
            print("     ➤ %s"
                  % ("⭐ KONZENTRIERT: der Median ist deutlich besser als "
                     "das Ankermittel - wenige Symbole tragen die Drift"
                     if np.median(werte) > dr_g + abs(dr_g) * 0.3
                     else "⚠️ BREIT: der Median liegt beim Ankermittel - "
                          "die Drift ist keine Teilmengenfrage"))
            print("     Verteilung: 10. %+.5f · 25. %+.5f · 50. %+.5f · "
                  "75. %+.5f · 90. %+.5f"
                  % tuple(np.percentile(werte, [10, 25, 50, 75, 90])))

        # ── ACHSE 3b: WEGLASSEN, zwei Fassungen ──────────────────────
        print("-" * 100)
        print("  ACHSE 3b  die schlechtesten Symbole WEGLASSEN - "
              "Rueckschau gegen KAUSAL")
        print("     ⛔ Rueckschau waehlt nach dem Ergebnis und ist KEINE "
              "Strategie; nur die kausale Spalte darf in eine Bewertung.")
        print("     weg    Rueckschau E[R]    KAUSAL (Vorjahr) E[R]")
        rangfolge = sorted(dr_je, key=lambda s: dr_je[s])
        # Vorjahresdrift je (Symbol, Jahr) - streng kausal
        vor = {}
        for sy in dr_je:
            ms = SYM == sy
            for j in sorted(set(JAHR[ms].tolist())):
                mj = ms & (JAHR == j)
                if mj.sum() >= 200:
                    vor[(sy, j)] = float(np.mean(RO[mj]))
        for anteil in WEGLASS:
            k = int(round(anteil * len(rangfolge)))
            raus = set(rangfolge[:k])
            m_r = np.array([s not in raus for s in SYM])
            er_r, _, _ = kennzahl(Z[m_r], S[m_r], RO[m_r], crv)
            # kausal: je Anker entscheidet die Drift des VORjahres
            behalte = np.ones(len(SYM), bool)
            if k:
                for j in sorted(set(JAHR.tolist())):
                    kand = {s: v for (s, jj), v in vor.items()
                            if jj == j - 1 and s in dr_je}
                    if not kand:
                        continue
                    schlecht = set(sorted(kand, key=lambda s: kand[s])
                                   [:max(1, int(round(anteil * len(kand))))])
                    if not schlecht:
                        continue
                    mj = JAHR == j
                    behalte[mj] = np.array(
                        [s not in schlecht for s in SYM[mj]])
            er_k, _, _ = kennzahl(Z[behalte], S[behalte], RO[behalte], crv)
            print("     %3.0f %%      %+.5f          %+.5f      %s"
                  % (100 * anteil, er_r, er_k,
                     "⭐⭐ KAUSAL POSITIV" if er_k > 0 else
                     ("(nur Rueckschau positiv)" if er_r > 0 else "-")))

    print()
    print("  ⚠️ Was diese Messung NICHT beantwortet: ob eine Lage innerhalb")
    print("     einer tragenden Teilmenge trennt. Das ist Schritt 3 und")
    print("     setzt voraus, dass hier eine Teilmenge mit E[R] > 0 gefunden")
    print("     wird - sonst gibt es keine Menge, auf der zu messen waere.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
