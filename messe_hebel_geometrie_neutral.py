# -*- coding: utf-8 -*-
"""Der neue Hebel-Arm, Schritt 1: eine LAGENEUTRALE Geometrie

**Nutzerauftrag 25.09.2026:** *"wir bauen den Hebel Arm vollstaendig neu.
Wenn Hebel funktioniert dann gehen wir zu den anderen Strategien."*

Dies ist das FUNDAMENT. Ohne es ist jede Lagemessung wertlos - Befund 2.596:

    Fuenftel nach momentum_kurz:  5 % Stop entspricht
        0,753 / 0,858 / 0,868 / 0,839 / 0,674 ATR

    ➤ Im obersten Fuenftel ist der Stop 22 % ENGER als im mittleren - und er
      liegt unter dem projekteigenen Rauschboden `stop_min_atr` = 0,75,
      dessen Begruendung woertlich lautet: *ein Stop innerhalb der
      Tagesspanne wird vom Zufall getroffen, nicht von einer Information*
      (RM-1c).

    ⚠️⚠️ Wer den Stop in PROZENT festschreibt, waehrend die Lage die
    Volatilitaet mitbestimmt, vergleicht nicht Lagen, sondern STOPWEITEN.

═══════════════════════════════════════════════════════════════════════
 ZWEI ABNAHMEPROBEN - beide muessen halten, sonst ist das Fundament schief
═══════════════════════════════════════════════════════════════════════

    PROBE 1  Der Stop ist in ATR-Einheiten in JEDER Lage gleich weit -
             GEPAART gegen den fixen Prozentstop gemessen.

             ⚠️⚠️ Die erste Fassung war eine TAUTOLOGIE: `clip(k x ATR)/ATR`
             IST k, solange die Klammer nicht bindet. Eine Spanne nahe null
             war damit kein Nachweis, sondern Arithmetik. Erst der FIX-Arm
             macht die Probe zu einer Probe - und er muss dabei Befund
             2.596 reproduzieren (R-R11).

    PROBE 2  Die Barriere aendert den Erwartungswert NICHT - gegen die
             DRIFT gemessen, nicht gegen null.

             ⚠️⚠️ Die erste Fassung verglich gegen null. Das gilt nur auf
             einem driftfreien Pfad, und 116 Kryptowerte ueber vier Jahre
             sind das nicht. Der richtige Bezug steckt in denselben Daten:
             `RO` ist die H-Stunden-Rendite in Stopabstaenden OHNE
             Barrieren. Eine Stoppregel auf einem Martingal aendert den
             Erwartungswert nicht (Optional Stopping).

⚠️ Und die Zahlen, die dazugehoeren:

    KLAMMER      wie oft bindet der Deckel? Ein Deckel, der in einer Lage
                 haeufiger greift, bringt die Lageabhaengigkeit durch die
                 Hintertuer zurueck. Je Fuenftel ausgewiesen.
    GLEICHSTAND  wie oft liegen beide Barrieren in DERSELBEN Stunde? Das
                 ist der Preis der Stop-zuerst-Konvention (2.583).
    ⭐ NULLBAND  40 Ziehungen mit ZUFALLSfuenftel, Bezug = Mittelwert,
                 Grenze = 90. Perzentil. OHNE DIESE ZEILE IST "NETTO IST
                 POSITIV" KEINE AUSSAGE.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ DIE ZIELGROESSE HEISST `E[R]` NETTO
═══════════════════════════════════════════════════════════════════════

    netto = E[R]  -  Drift(Halten)      je Fuenftel, gleiche Einheit

⚠️⚠️ **2.595 hat `E[R]` gegen NULL verglichen** und daraus geschlossen, die
beste Lage sei die schlechteste (-0,0091 gegen -0,0056). Gemessen ist aber:
`E[R]_alle` folgt der Drift fast exakt. Ein `E[R]` von -0,009 ist kein
schlechtes Geschaeft, wenn das blosse Halten -0,014 bringt.

═══════════════════════════════════════════════════════════════════════
 DIE GEOMETRIE
═══════════════════════════════════════════════════════════════════════

    atr_tag_rel   mittlere Stundenspanne (high-low)/close der letzten 24 h,
                  mit Wurzel 24 auf ein Tagesmass skaliert
    stop_rel      k x atr_tag_rel, geklammert auf [2 %, 25 %]
    ziel_rel      CRV x stop_rel
    k             0,75 / 1,0 / 1,5      (0,75 = der Rauschboden)
    CRV           1,5 / 2,0 / 3,0 / 4,0 (2.596: bei q = 0,24 braeuchte es
                                         CRV > 3,16)

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_hebel_geometrie_neutral.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, merkmale_je_symbol)
from messe_q_beide_seiten import (                              # noqa: E402
    fuenftel_je_stunde, MIND_JE_FUENFTEL)

#: ⭐⭐ Die Geometrien LAUFEN GEPAART - derselbe Anker, dieselbe Ankermenge.
#:
#: ⚠️⚠️ Ohne den FIX-Arm ist PROBE 1 eine Tautologie: `clip(k x ATR)/ATR`
#: IST k, solange die Klammer nicht bindet. Eine Spanne nahe null waere dann
#: kein Nachweis, sondern Arithmetik. Erst der Vergleich gegen den fixen
#: Prozentstop zeigt, ob der Umbau etwas repariert - und er muss dabei
#: Befund 2.596 REPRODUZIEREN (R-R11):
#:
#:      5 % fix, Fuenftel nach momentum_kurz:
#:          0,753 / 0,858 / 0,868 / 0,839 / 0,674 ATR
GEOMETRIEN = (("ATR", 0.75), ("ATR", 1.0), ("ATR", 1.5),
              ("FIX", 0.05), ("FIX", 0.08))
CRVS = (1.5, 2.0, 3.0, 4.0)
HORIZONTE = (6, 12, 24)
STOP_MIN, STOP_MAX = 0.02, 0.25
VORLAUF = 30
SAAT = 20260925
#: Nullband nur im LAGENEUTRALEN Arm (k = 1,0) und nur dort, wo die Frage
#: entschieden wird - 40 Ziehungen kosten Zeit, und in den Armen, die
#: PROBE 1 nicht bestehen, waere die Antwort ohnehin nicht verwertbar.
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
NULL_CRVS = (1.5, 2.0, 3.0)
#: Positivkontrolle: 5 Ziehungen je Stufe (Messstandard).
N_POSITIV = 5
#: Stufe 0,00 ist die Positivkontrolle nach unten - sie DARF nicht trennen.
STAERKEN = (0.0, 0.05, 0.10, 0.25, 0.50, 1.0)


def atr_tag_relativ(high, low, close):
    """Mittlere Stundenspanne der letzten 24 h, auf Tagesmass skaliert.

    ⚠️ Streng kausal: der Wert zur Stunde t nutzt nur Stunden <= t. Die
    Wurzel-24-Skalierung ist eine NAEHERUNG (Irrfahrt) und dient nur dazu,
    die Zahl mit dem projekteigenen `stop_min_atr` vergleichbar zu machen -
    fuer die Neutralitaet selbst ist sie unerheblich, weil sie ein
    konstanter Faktor ist.
    """
    n = len(close)
    sp = (high - low) / np.maximum(close, 1e-12)
    k = np.ones(24) / 24.0
    m = np.convolve(sp, k, mode="full")[:n]
    m[:24] = np.nan
    return m * np.sqrt(24.0)


def ausgaenge(high, low, close, stop_rel, ziel_rel, H):
    """-> (ist_ziel, ist_stop, r_offen, gueltig, gleichstand).

    Stop zuerst (2.583) - und genau das ist NICHT neutral. Wenn in
    derselben Stunde beide Barrieren im Spannenbereich liegen, bekommt der
    Stop den Zuschlag. `gleichstand` zaehlt diese Faelle, weil sie die
    EINZIGE hergeleitete Erklaerung dafuer sind, dass `E[R]_alle` unter
    null liegt - und weil ihr Anteil mit dem Horizont waechst.

    ⚠️ Ohne diese Zahl ist PROBE 2 nicht auswertbar: man saehe eine
    Abweichung und wuesste nicht, ob sie ein Fehler oder die eigene
    Konvention ist.
    """
    n = len(close)
    gueltig = np.isfinite(stop_rel) & (stop_rel > 0)
    gueltig[:VORLAUF] = False
    gueltig[max(0, n - max(HORIZONTE)):] = False
    idx = np.arange(n)
    stop_kurs = close * (1.0 - stop_rel)
    ziel_kurs = close * (1.0 + ziel_rel)
    fertig = ~gueltig.copy()
    ist_ziel = np.zeros(n, bool)
    ist_stop = np.zeros(n, bool)
    gleich = np.zeros(n, bool)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        offen = ~fertig
        if not offen.any():
            break
        s_hit = offen & (low[j] <= stop_kurs)
        z_roh = offen & (high[j] >= ziel_kurs)
        gleich |= (s_hit & z_roh)          # beide in DERSELBEN Stunde
        z_hit = z_roh & ~s_hit
        ist_stop |= s_hit
        ist_ziel |= z_hit
        fertig |= (s_hit | z_hit)
    je = np.minimum(idx + H, n - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r_offen = (close[je] / np.maximum(close, 1e-12) - 1.0) / np.maximum(
            stop_rel, 1e-12)
    return (ist_ziel & gueltig, ist_stop & gueltig, r_offen, gueltig,
            gleich & gueltig)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("DER NEUE HEBEL-ARM, SCHRITT 1: EINE LAGENEUTRALE GEOMETRIE")
    print("=" * 100)
    print("  Stop geklammert [%.0f %%, %.0f %%] · CRV %s · H %s"
          % (100 * STOP_MIN, 100 * STOP_MAX,
             "/".join("%.1f" % x for x in CRVS),
             "/".join("%d" % x for x in HORIZONTE)))
    print("  Geometrien GEPAART: %s"
          % " · ".join("%s %.2f" % (a, x) for a, x in GEOMETRIEN))
    print("  ⚠️ Der FIX-Arm ist der Vergleichsarm (R-R11): er muss 2.596")
    print("     reproduzieren - 5 %% fix sind im obersten Momentumfuenftel")
    print("     nur 0,674 ATR gegen 0,868 im mittleren.")

    #: [gefunden, gezogen] bei Staerke 0,00 ueber ALLE Zellen -
    #: nur diese Summe eicht die Anlage, nicht die Einzelzelle.
    FEHL = [0, 0]

    kurse = lade_kurse(grenze)
    print("  %d Symbole geladen" % len(kurse), flush=True)

    # ── alles einmal aufbereiten ──────────────────────────────────────
    sid: dict = {}
    roh = []
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        atr = atr_tag_relativ(high, low, close)
        m = merkmale_je_symbol(sym, stunden, high, low, close, volumen,
                              {}, {})
        roh.append((sym, stunden, high, low, close, atr,
                    m.get("momentum_kurz")))
        for s_ in stunden:
            if s_ not in sid:
                sid[s_] = len(sid)

    for art, k in GEOMETRIEN:
        for crv in CRVS:
            for H in HORIZONTE:
                G, Z, S, RO, MOM, ATR, KLAMM = [], [], [], [], [], [], []
                STOPR, GL = [], []
                for (sym, stunden, high, low, close, atr, mom) in roh:
                    if art == "ATR":
                        roh_stop = k * atr
                    else:
                        # ⚠️ NaN dort, wo auch der ATR-Arm keinen Wert hat -
                        # sonst waere die Ankermenge eine andere und der
                        # Vergleich verglichen zwei Mengen statt zwei
                        # Geometrien.
                        roh_stop = np.where(np.isfinite(atr), k, np.nan)
                    stop_rel = np.clip(roh_stop, STOP_MIN, STOP_MAX)
                    geklammert = (roh_stop < STOP_MIN) | (roh_stop > STOP_MAX)
                    zz, ss, ro, gu, gl = ausgaenge(high, low, close, stop_rel,
                                                   crv * stop_rel, H)
                    sel = np.flatnonzero(gu & np.isfinite(
                        mom if mom is not None else np.zeros(len(close))))
                    if not len(sel):
                        continue
                    G.append(np.array([sid[stunden[i]] for i in sel],
                                      np.int64))
                    Z.append(zz[sel]); S.append(ss[sel]); RO.append(ro[sel])
                    MOM.append(mom[sel]); ATR.append(atr[sel])
                    KLAMM.append(geklammert[sel])
                    STOPR.append(stop_rel[sel]); GL.append(gl[sel])
                if not G:
                    continue
                G = np.concatenate(G); Z = np.concatenate(Z)
                S = np.concatenate(S); RO = np.concatenate(RO)
                MOM = np.concatenate(MOM); ATR = np.concatenate(ATR)
                KLAMM = np.concatenate(KLAMM)
                STOPR = np.concatenate(STOPR); GL = np.concatenate(GL)
                #: der Stop in ATR-Einheiten - im ATR-Arm per Konstruktion
                #: k, im FIX-Arm die Zahl, die 2.596 gemessen hat
                IN_ATR = STOPR / np.maximum(ATR, 1e-9)
                r = np.where(Z, crv, np.where(S, -1.0, np.nan_to_num(RO)))
                geloest = Z | S
                print()
                print("-" * 100)
                # ── PROBE 2, HERGELEITET statt gesetzt ────────────────
                #
                # ⛔⛔ Die erste Fassung verglich `E[R]_alle` gegen NULL.
                # Das war falsch: null gilt nur auf einem DRIFTFREIEN Pfad,
                # und 116 Kryptowerte von 2021-12 bis 2026-09 sind das
                # nicht. Gemessen am kleinen Lauf: Gleichstand 0,02 %
                # deckt -0,0004, gemessen wurden -0,0037 bis -0,0182 -
                # Faktor 10 bis 45. Die Konvention erklaert es nicht.
                #
                # ⭐ Der richtige Bezug liegt in denselben Daten: `RO` ist
                # die H-Stunden-Rendite in Stopabstaenden fuer JEDEN
                # gueltigen Anker, OHNE Barrieren. Eine Stoppregel auf
                # einem Martingal aendert den Erwartungswert nicht
                # (Optional Stopping). Also:
                #
                #       E[R]_alle  gegen  mean(RO)      statt gegen 0
                #
                # Beide auf derselben Menge, in derselben Einheit. Bleibt
                # ein Rest, ist er der Konvexitaetseffekt plus Gleichstand
                # - und der Gleichstand ist jetzt ausgewiesen.
                er = float(r.mean())
                drift = float(np.mean(RO))
                gl_anteil = float(GL.mean())
                rest = er - drift
                deckel = gl_anteil * (1.0 + crv)
                if abs(rest) <= max(deckel, 0.002):
                    urteil = "✔ PROBE 2: Barriere aendert E[R] nicht"
                else:
                    urteil = "⚠️ PROBE 2: Rest %+.5f unerklaert" % rest
                etikett = ("k %.2f x ATR" % k if art == "ATR"
                           else "FIX %.0f %% (2.596)" % (100 * k))
                print("%-18s · CRV %.1f · H%d · %d Anker · "
                      "Stop Median %.2f %% · Klammer bindet %.1f %%"
                      % (etikett, crv, H, len(G),
                         100 * float(np.nanmedian(STOPR)),
                         100 * KLAMM.mean()))
                print("   Aufloesung %.1f %% · q_alle %.4f · "
                      "⭐ E[R]_alle %+.5f · Drift ohne Barriere %+.5f · "
                      "Gleichstand %.3f %%"
                      % (100 * geloest.mean(),
                         Z.sum() / max(1, geloest.sum()), er, drift,
                         100 * gl_anteil))
                print("   %s" % urteil)
                # ── PROBE 1: ist der Stop in jeder Lage gleich weit? ──
                fz = fuenftel_je_stunde(G, MOM)
                if fz is None:
                    print("   zu duenn fuer Fuenftel")
                    continue
                idx, f = fz
                nk = np.bincount(f, minlength=5).astype(float)
                if (nk < MIND_JE_FUENFTEL).any():
                    print("   zu duenn fuer Fuenftel")
                    continue
                stop_je = np.bincount(f, weights=STOPR[idx],
                                      minlength=5) / nk
                in_atr = np.bincount(f, weights=IN_ATR[idx],
                                     minlength=5) / nk
                gl_f = np.bincount(f, weights=GL[idx].astype(float),
                                   minlength=5) / nk
                kl_je = np.bincount(f, weights=KLAMM[idx].astype(float),
                                    minlength=5) / nk
                zk = np.bincount(f, weights=Z[idx].astype(float),
                                 minlength=5)
                sk = np.bincount(f, weights=S[idx].astype(float),
                                 minlength=5)
                rk = np.bincount(f, weights=r[idx], minlength=5) / nk
                #: ⭐⭐⭐ Der Drift je Fuenftel - und DAS ist der Nullpunkt.
                #: Ein `E[R]` von -0,009 im obersten Fuenftel ist KEIN
                #: schlechtes Geschaeft, wenn das blosse Halten dort
                #: -0,014 bringt. 2.595 hat gegen null verglichen und
                #: daraus geschlossen, die beste Lage sei die schlechteste.
                dk = np.bincount(f, weights=RO[idx], minlength=5) / nk
                netto = rk - dk
                lo = zk + sk
                q = np.where(lo >= MIND_JE_FUENFTEL, zk / np.maximum(lo, 1),
                             np.nan)
                print("   Fuenftel nach momentum_kurz   0        1        "
                      "2        3        4")
                spanne = float(in_atr.max() - in_atr.min())
                print("      Stop in ATR      %s   ⭐ PROBE 1: Spanne %.4f  %s"
                      % (" ".join("%8.4f" % x for x in in_atr), spanne,
                         "✔ neutral" if spanne < 0.02 else "⚠️ NICHT neutral"))
                if art == "ATR":
                    print("        ⚠️ im ATR-Arm ist diese Zeile per "
                          "Konstruktion k - sie prueft nur die KLAMMER. "
                          "Der Nachweis steht im FIX-Arm.")
                print("      Stop in %%        %s"
                      % " ".join("%8.3f" % (100 * x) for x in stop_je))
                print("      Klammer %%       %s"
                      % " ".join("%8.3f" % (100 * x) for x in kl_je))
                print("      Gleichstand %%   %s"
                      % " ".join("%8.3f" % (100 * x) for x in gl_f))
                print("      q               %s" % " ".join("%8.4f" % x
                                                            for x in q))
                print("      E[R]            %s" % " ".join("%+8.4f" % x
                                                            for x in rk))
                print("      Drift (Halten)  %s" % " ".join("%+8.4f" % x
                                                            for x in dk))
                print("      ⭐ E[R] NETTO   %s   Spanne %+.4f"
                      % (" ".join("%+8.4f" % x for x in netto),
                         float(netto[4] - netto[:4].mean())))
                print("      ➤ Kelly-Nullstelle %.4f · q4 %s · "
                      "E[R]4 brutto %s · ⭐ NETTO %s"
                      % (1.0 / (1.0 + crv),
                         "UEBER" if q[4] > 1.0 / (1.0 + crv) else "unter",
                         "POSITIV" if rk[4] > 0 else "negativ",
                         "POSITIV" if netto[4] > 0 else "negativ"))

                # ── NULLBAND nach Messstandard ────────────────────────
                #
                # ⚠️⚠️⚠️ OHNE DIESE ZEILEN IST "NETTO IST POSITIV" KEINE
                # AUSSAGE. Eine Spanne von +0,0021 kann reines Rauschen
                # sein - und genau dieser Fehler ist in dieser Messreihe
                # schon einmal passiert (2.592, auf 120 statt 3237922
                # Reihen gemessen).
                #
                # Die Nullwelt zieht das FUENFTEL zufaellig, behaelt aber
                # die Stundenklammer und die Fuenftelgroessen. Damit ist
                # sie genau die Frage "ordnet `momentum_kurz` besser als
                # ein Wuerfel?" - nicht "ist die Zahl gross?".
                #
                # Bezug = MITTELWERT der Nullwelten (Standard seit 2.216);
                # das 90. Perzentil ist die ausgewiesene obere Grenze.
                if not (art == "ATR" and abs(k - 1.0) < 1e-9
                        and crv in NULL_CRVS):
                    continue
                rng = np.random.default_rng(SAAT + H + int(100 * crv))
                nullw = []
                for _ in range(N_NULL):
                    fzz = fuenftel_je_stunde(G, rng.random(len(G)))
                    if fzz is None:
                        continue
                    i2, f2 = fzz
                    n2 = np.bincount(f2, minlength=5).astype(float)
                    if (n2 < MIND_JE_FUENFTEL).any():
                        continue
                    r2 = np.bincount(f2, weights=r[i2], minlength=5) / n2
                    d2 = np.bincount(f2, weights=RO[i2], minlength=5) / n2
                    nt = r2 - d2
                    nullw.append(float(nt[4] - nt[:4].mean()))
                if len(nullw) < 10:
                    print("      ⚠️ Nullband nicht zu bilden (%d Ziehungen)"
                          % len(nullw))
                    continue
                nullw = np.array(nullw)
                nullpunkt = float(nullw.mean())
                null90 = float(np.percentile(nullw, NULL_PERZ))
                gemessen = float(netto[4] - netto[:4].mean())
                print("      ⭐⭐ NULLBAND %d Ziehungen · Nullpunkt %+.5f · "
                      "%d. Perzentil %+.5f · gemessen %+.5f"
                      % (len(nullw), nullpunkt, NULL_PERZ, null90, gemessen))
                print("         ➤ %s   (Faktor %.1f ueber dem Band)"
                      % ("✔✔ TRENNT gegen den Nullpunkt"
                         if gemessen > null90
                         else "⛔ liegt IM Nullband - keine Aussage",
                         abs(gemessen - nullpunkt)
                         / max(abs(null90 - nullpunkt), 1e-12)))

                # ── TRENNSCHAERFE / POSITIVKONTROLLE ──────────────────
                #
                # Der Standard verlangt beides. Hier in EINER Leiter: das
                # echte Merkmal wird stufenweise in den Zufall gemischt.
                #
                #     staerke = 0   ->  reine Nullwelt (muss NICHT trennen)
                #     staerke = 1   ->  das echte Merkmal
                #
                # ⭐ Was das beantwortet: ab welchem Anteil echter Ordnung
                # schlaegt die Anlage an? Das ist die Nachweisgrenze in der
                # Einheit, in der die Frage gestellt ist - und die Stufe
                # 0,0 ist gleichzeitig die Positivkontrolle nach unten
                # (sie DARF nicht trennen).
                # ⚠️⚠️ JE STUFE MEHRERE ZIEHUNGEN - eine einzige ist bei
                # einem 90.-Perzentil-Band eine Muenze. Die erste Fassung
                # zog einmal je Stufe und meldete daraufhin bei Stufe 0,00
                # einen Fund (erwartet: 10 % von 6 Zellen = 0,6, beobachtet
                # 1 - im Rahmen, aber als Leiter unbrauchbar).
                #
                # Ausgewiesen wird der MEDIAN und die FUNDQUOTE. Die Norm
                # nennt 80 % Fundquote als Auflösungspunkt.
                rg = np.argsort(np.argsort(MOM)) / max(1, len(MOM) - 1)
                print("      ⭐⭐ TRENNSCHAERFE - Anteil echter Ordnung, "
                      "%d Ziehungen je Stufe" % N_POSITIV)
                for staerke in STAERKEN:
                    werte = []
                    for _ in range(N_POSITIV):
                        mix = (staerke * rg
                               + (1.0 - staerke) * rng.random(len(G)))
                        fzm = fuenftel_je_stunde(G, mix)
                        if fzm is None:
                            continue
                        i3, f3 = fzm
                        n3 = np.bincount(f3, minlength=5).astype(float)
                        if (n3 < MIND_JE_FUENFTEL).any():
                            continue
                        r3 = np.bincount(f3, weights=r[i3], minlength=5) / n3
                        d3 = np.bincount(f3, weights=RO[i3], minlength=5) / n3
                        nt3 = r3 - d3
                        werte.append(float(nt3[4] - nt3[:4].mean()))
                    if not werte:
                        continue
                    werte = np.array(werte)
                    quote = float((werte > null90).mean())
                    # ⚠️ Bei Stufe 0,00 wird NICHT je Zelle geurteilt. Mit
                    # 5 Ziehungen sind nur 0/20/40/60/80/100 % moeglich,
                    # und P(>=2 von 5 bei 10 %) = 8 % - eine einzelne
                    # Zelle mit 40 % ist Clusterung, kein Fehlalarm. Die
                    # Zahl, die zaehlt, steht in der Summenzeile unten.
                    print("         Anteil %.2f -> Median %+.5f · "
                          "Fundquote %3.0f %%   %s"
                          % (staerke, float(np.median(werte)), 100 * quote,
                             "(Nullstufe - Summe zaehlt)" if staerke == 0.0
                             else ("✔ aufgeloest" if quote >= 0.8
                                   else "- unter Grenze")))
                    if staerke == 0.0:
                        FEHL[0] += int((werte > null90).sum())
                        FEHL[1] += len(werte)
    print()
    if FEHL[1]:
        quote = FEHL[0] / FEHL[1]
        soll = 1.0 - NULL_PERZ / 100.0
        print()
        print("  ⭐⭐ POSITIVKONTROLLE gesamt: %d von %d Nullziehungen als Fund"
              % (FEHL[0], FEHL[1]))
        print("     gemeldet = %.1f %% · Soll %.1f %% (das Band IST das %d. Perzentil)"
              % (100 * quote, 100 * soll, int(NULL_PERZ)))
        print("     ➜ %s"
              % ("✔✔ GEEICHT" if quote <= 2.5 * soll
                 else "⚠️ Fehlalarmquote zu hoch"))

    print("  ⚠️ PROBE 1 ist die Voraussetzung: erst wenn der Stop in jeder")
    print("     Lage gleich weit ist, vergleicht die Messung LAGEN.")
    print("  ⚠️ PROBE 2 ist die Plausibilitaet: ein Barrierensystem hat")
    print("     Erwartungswert null. Eine deutliche Abweichung ist ein")
    print("     Hinweis auf einen Fehler, nicht auf eine Kante.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
