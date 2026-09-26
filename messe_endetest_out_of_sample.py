# -*- coding: utf-8 -*-
"""DER ENDE-ZU-ENDE-TEST: traegt die Kalibrierung auf ungesehenen Daten?

**26.09.2026**, Nutzerauftrag: *"vor der Verdrahtung haette ich gerne einen
ausfuehrlichen Test ob unsere Bewertungen, Kalibrierung, bei echten Daten
auch das Ergebnis liefert dass es soll"* - *"langsam und sorgsam, keine
Fehler, pruefen und gegenpruefen"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_23_Endetest_26_09.md`

═══════════════════════════════════════════════════════════════════════
 ⛔ WARUM ALLES BISHERIGE DEN TEST NICHT ERSETZT
═══════════════════════════════════════════════════════════════════════

2.608 (Einstieg), 2.620 (Geometrie) und 2.622 (`q`) sind jeder fuer sich
gemessen - und ALLE IN-SAMPLE. Die Baender wurden auf denselben Daten
gebildet, auf denen sie gemessen wurden. Das ist Kurvenanpassung, bis das
Gegenteil gezeigt ist.

⚠️ B6 hilft hier NICHT: es prueft, ob ein Befund in beiden Haelften GILT -
nicht, ob eine auf A KALIBRIERTE Tabelle auf B TRAEGT. Das ist ein
Unterschied, und er entscheidet alles.

═══════════════════════════════════════════════════════════════════════
 DIE KONSTRUKTION
═══════════════════════════════════════════════════════════════════════

    ROLLIEREND, nicht ein Split (Falle 5): fuenf Fenster, jeweils auf dem
    vorangegangenen kalibriert und auf dem folgenden geprueft. So haengt
    das Ergebnis nicht an einem Schnittpunkt.

    ⚠️⚠️ MIT LUECKE (Falle 4): zwischen Kalibrier- und Prueffenster bleiben
    H Stunden frei. Ein Anker am Ende des Kalibrierfensters saehe sonst
    drei Tage in das Prueffenster hinein - seine Zielgroesse kaeme
    teilweise aus Daten, die als ungesehen gelten sollen.

    ⚠️ DIE GEOMETRIE WIRD MITKALIBRIERT, nicht uebernommen (Falle 1). Alles
    aus 2.620 wurde auf der VOLLEN Menge bestimmt; sie zu uebernehmen hiesse,
    Wissen ueber das Prueffenster einzuschleusen. Das macht den Test
    strenger als noetig, und genau das ist gewollt.

    ⚠️ `q` UND CRV AUS DERSELBEN HAELFTE (Falle 2, aus 2.622): die gemessene
    Quote mit einem fremden CRV zu mischen ueberschaetzt Kelly um 71 %.

═══════════════════════════════════════════════════════════════════════
 DER MASSSTAB - VORHER FESTGELEGT (Falle 3)
═══════════════════════════════════════════════════════════════════════

    HAUPTGROESSE   geometrischer Ertrag je Trade im Prueffenster
    VERGLEICH      dieselbe Kette mit ZUFALLSAUSWAHL gleicher Groesse
    BESTANDEN      ueber dem 90. Perzentil der Zufallskette
    ⭐ SCHAERFER   trifft das vorhergesagte `q`? Verspricht die Tabelle 48 %
                   und es treten 41 % ein, ist sie wertlos - unabhaengig
                   vom Ertrag.

⚠️ NUR LESEN.  python messe_endetest_out_of_sample.py [--symbole N]
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
    trailing_mit_ausloeser, geometrisch, laengste_verlustserie,
    EMA_L, VORLAUF)

H = 72
FENSTER = 5
#: klein gehalten, weil je Fenster neu kalibriert wird
STOPWEITEN = (0.75, 1.0, 1.5)
AUSLOESER = (1.0, 1.5)
ABSTAND = 0.5
#: die Baender, fuer die `q` kalibriert wird (aus 2.622)
BAENDER = ((0.5, 0.7), (0.7, 0.9), (0.9, 1.1), (1.1, 1.3), (1.3, 9e9))
SCHWELLE = 0.9          # ab hier wird gehandelt - Kelly ist darunter klein
MIND_BAND = 100
SAAT = 20260926


def kennzahlen(r):
    """-> (q, crv, kelly) aus einer Ergebnisreihe. EINE Stelle, kein Duplikat."""
    if not len(r):
        return float("nan"), float("nan"), float("nan")
    p = float((r > 0).mean())
    g, v = r[r > 0], r[r <= 0]
    if not len(g) or not len(v) or v.mean() == 0:
        return p, float("nan"), float("nan")
    b = float(g.mean() / abs(v.mean()))
    return p, b, (p * (1.0 + b) - 1.0) / b


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 104)
    print("DER ENDE-ZU-ENDE-TEST - OUT OF SAMPLE")
    print("=" * 104)
    print("  " + N.standardzeile())
    print("  %d rollierende Fenster · Luecke %d h zwischen Kalibrierung "
          "und Pruefung" % (FENSTER, H))
    print("  ⚠️ Die GEOMETRIE wird je Fenster MITKALIBRIERT - nichts aus "
          "2.620 uebernommen")
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}

    # ── einmal alles vorbereiten, dann nur noch Masken ───────────────
    roh = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        sel = np.flatnonzero(gu)
        if len(sel):
            roh.append((np.array([sid[x] for x in st], np.int64),
                        h, l, cc, atr, w, sel))
    G = np.concatenate([d[0][d[6]] for d in roh])
    W = np.concatenate([d[5][d[6]] for d in roh])
    n = len(G)
    print("  %d Symbole · %d Anker" % (len(roh), n), flush=True)

    # ── die Ergebnisreihen je Geometriezelle EINMAL rechnen ──────────
    # ⚠️ Das ist der teure Teil; die Fenster sind danach nur Masken.
    print("  rechne %d Geometriezellen ..." % (len(STOPWEITEN) * len(AUSLOESER)),
          flush=True)
    zellen = {}
    for weite in STOPWEITEN:
        for ausl in AUSLOESER:
            rr = []
            for idx, h, l, cc, atr, w, sel in roh:
                a, _p, _d = trailing_mit_ausloeser(h, l, cc, atr, weite,
                                                   ausl, ABSTAND, H)
                rr.append(a[sel])
            zellen[(weite, ausl)] = np.concatenate(rr)
            print("    Stop %.2f / Ausloeser %.1f fertig" % (weite, ausl),
                  flush=True)

    # ── die Fenstergrenzen ───────────────────────────────────────────
    stunden = np.sort(np.unique(G))
    kanten = np.linspace(0, len(stunden) - 1, FENSTER + 1).astype(int)
    grenzen = [stunden[k] for k in kanten]

    rng = np.random.default_rng(SAAT)
    print()
    print("=" * 104)
    print("DIE ROLLIERENDEN FENSTER")
    print()
    bestanden = 0
    laeufe = 0
    for i in range(FENSTER - 1):
        kal = (G >= grenzen[i]) & (G < grenzen[i + 1])
        # ⚠️⚠️ FALLE 4: die Luecke. Ein Anker am Ende des Kalibrierfensters
        # saehe sonst H Stunden in das Pruefffenster hinein.
        pru = (G >= grenzen[i + 1] + H) & (G < grenzen[i + 2])
        if kal.sum() < 5000 or pru.sum() < 5000:
            continue
        laeufe += 1
        print("  FENSTER %d  kalibrieren auf %d Ankern, pruefen auf %d "
              "(Luecke %d h)" % (i + 1, int(kal.sum()), int(pru.sum()), H))

        # ── 1. GEOMETRIE auf der Kalibrierhaelfte waehlen ────────────
        beste, bester_wert = None, -9e9
        for schl, r in zellen.items():
            m = kal & np.isfinite(W) & (W >= SCHWELLE)
            if m.sum() < 200:
                continue
            g = geometrisch(r[m])
            if g > bester_wert:
                bester_wert, beste = g, schl
        if beste is None:
            print("    (zu wenige Signale)"); continue
        r_all = zellen[beste]
        print("    gewaehlte Geometrie: Stop %.2f / Ausloeser %.1f  "
              "(geom %+.5f %% in der Kalibrierung)"
              % (beste[0], beste[1], 100 * bester_wert))

        # ── 2. q-TABELLE auf der Kalibrierhaelfte ────────────────────
        tab = {}
        for lo, hi in BAENDER:
            m = kal & np.isfinite(W) & (W >= lo) & (W < hi)
            if m.sum() < MIND_BAND:
                continue
            tab[(lo, hi)] = kennzahlen(r_all[m])

        # ── 3. ANWENDEN auf der Pruefhaelfte ─────────────────────────
        print("    %-12s %9s %9s %9s %9s  %s"
              % ("Band", "q erwart", "q eingetr", "Kelly erw", "Kelly ein",
                 "Urteil"))
        treffer = 0; geprueft = 0
        for (lo, hi), (q_e, b_e, k_e) in sorted(tab.items()):
            m = pru & np.isfinite(W) & (W >= lo) & (W < hi)
            if m.sum() < MIND_BAND:
                continue
            q_i, b_i, k_i = kennzahlen(r_all[m])
            # Band um die erwartete Quote: Binomialstreuung der Pruefmenge
            se = float(np.sqrt(max(q_e * (1 - q_e), 1e-9) / m.sum()))
            trifft = abs(q_i - q_e) <= 1.96 * se
            geprueft += 1; treffer += 1 if trifft else 0
            print("    %-12s %8.1f%% %8.1f%% %9.4f %9.4f  %s"
                  % ("%.1f-%.1f" % (lo, hi if hi < 9 else 9.9),
                     100 * q_e, 100 * q_i, k_e, k_i,
                     "✔ trifft" if trifft else "⛔ daneben (±%.1f Pp)"
                     % (100 * 1.96 * se)))

        # ── 4. DIE KETTE: geometrischer Ertrag gegen Zufall ──────────
        sig = pru & np.isfinite(W) & (W >= SCHWELLE)
        k = int(sig.sum())
        if k >= 200:
            frei = np.flatnonzero(pru & np.isfinite(W))

            # ⚠️⚠️⚠️ DIE NULLWELT ERHAELT DIE TAGESSTRUKTUR (Messstandard,
            # `messnorm`: *nur die Tagesklammer ist zulaessig*, null_
            # konstruktion = *Raenge je Tag gemischt*). Frei gezogene Anker
            # zerstoeren die Clusterung - echte Signale haeufen sich an
            # wenigen Tagen (Median 7, Maximum 620), Zufallsziehungen nicht.
            # Gemessen kostet das: *gepoolt statt Tagesklammer -> 12,4
            # Punkte auf einem Nulleffekt* (messnorm.py:454).
            #
            # ➤ Gezogen wird deshalb JE TAG so viele Anker, wie die echte
            # Auswahl an diesem Tag hat - nur WELCHE ist zufaellig.
            tag_frei = G[frei] // 24
            tag_sig = G[sig] // 24
            je_tag = {}
            for t, c in zip(*np.unique(tag_sig, return_counts=True)):
                je_tag[int(t)] = int(c)
            nach_tag = {}
            for i_, t in enumerate(tag_frei):
                nach_tag.setdefault(int(t), []).append(frei[i_])
            nach_tag = {t: np.array(v) for t, v in nach_tag.items()}

            def zieh_tagestreu():
                aus = []
                for t, c in je_tag.items():
                    pool = nach_tag.get(t)
                    if pool is None or not len(pool):
                        continue
                    aus.append(rng.choice(pool, size=min(c, len(pool)),
                                          replace=False))
                return np.concatenate(aus) if aus else np.array([], int)

            # ⭐⭐ BEIDE NULLWELTEN, und die Differenz wird hingeschrieben
            # (registrierte Regel *Gewichtung ausweisen: Tagesklammer oder
            # gepoolt*). Sie beantworten VERSCHIEDENE Fragen:
            #
            #   TAGESTREU  "waren die ausgewaehlten Anker besser als andere
            #              AM SELBEN TAG?" - die Auswahl allein.
            #   GEPOOLT    "war die Auswahl besser als der Durchschnitt?" -
            #              Auswahl PLUS die Wahl der Tage.
            #
            # ⚠️ Nutzervorgabe 26.09.: *an sehr guten Tagen kommen auch mehr
            # Signale, im Baerenmarkt wenige oder keine* - die Tageswahl ist
            # damit erwartetes Verhalten und nicht wegzurechnen. Der
            # Messstandard verlangt umgekehrt die Tagesklammer, weil gepoolt
            # 12,4 Punkte auf einem Nulleffekt erzeugt. BEIDES GILT, und
            # deshalb steht beides da.
            nb = np.array([geometrisch(r_all[zieh_tagestreu()])
                           for _ in range(N.NULL_ZIEHUNGEN)])
            nb_pool = np.array([geometrisch(
                r_all[rng.choice(frei, size=k, replace=False)])
                for _ in range(N.NULL_ZIEHUNGEN)])
            # ⚠️⚠️ MESSSTANDARD (messnorm.standardzeile): der BEZUG ist der
            # NULLPUNKT - der Mittelwert der Nullwelten -, das 90. Perzentil
            # ist die ausgewiesene obere Grenze. Beides gehoert ausgewiesen,
            # und die TRENNSCHAERFE misst gegen denselben Bezug (Fehler 2
            # vom 08.09.: Urteil und Trennschaerfe liefen auseinander).
            nullpunkt = float(nb.mean())
            b90 = float(np.percentile(nb, N.NULL_PERZENTIL))
            trennschaerfe = b90 - nullpunkt
            ge = geometrisch(r_all[sig])
            ok = ge > b90
            bestanden += 1 if ok else 0
            print("    KETTE: %d Signale · geom %+.5f %%" % (k, 100 * ge))
            np_p = float(nb_pool.mean())
            b90_p = float(np.percentile(nb_pool, N.NULL_PERZENTIL))
            ok_p = ge > b90_p
            print("           TAGESTREU (Standard): Nullpunkt %+.5f %% · "
                  "Band90 %+.5f %% · Trennschaerfe %.5f %% · %s"
                  % (100 * nullpunkt, 100 * b90, 100 * trennschaerfe,
                     "✔" if ok else "⛔ im Band"))
            print("             Abstand %+.5f %% (%.1fx Trennschaerfe)"
                  % (100 * (ge - nullpunkt),
                     (ge - nullpunkt) / max(trennschaerfe, 1e-12)))
            print("           GEPOOLT (Tageswahl zaehlt mit): Nullpunkt "
                  "%+.5f %% · Band90 %+.5f %% · %s"
                  % (100 * np_p, 100 * b90_p, "✔" if ok_p else "⛔ im Band"))
            print("           ➤ DIFFERENZ der Nullpunkte: %+.5f Pp - so viel "
                  "traegt allein die TAGESWAHL" % (100 * (nullpunkt - np_p)))
            print("           q-Treffer %d von %d Baendern · Serie %d"
                  % (treffer, geprueft,
                     laengste_verlustserie(r_all[sig])))

            # ── POSITIVKONTROLLE (Messstandard: 5 Ziehungen) ─────────
            #
            # ⚠️ Ohne sie weiss man nicht, ob der Test einen ECHTEN Effekt
            # ueberhaupt FINDEN wuerde. Gepflanzt wird auf der Pruefmenge
            # ein bekannter Zuschlag auf die ausgewaehlten Anker; der Test
            # muss ihn in allen Ziehungen ueber dem Band wiederfinden.
            # ⚠️ AUCH TAGESTREU - sonst prueft die Positivkontrolle einen
            # anderen Prueftstand als das Urteil.
            gefunden = 0
            for _z in range(5):
                zus = zieh_tagestreu()
                gepflanzt = r_all.copy()
                gepflanzt[zus] += 0.10          # +0,10 R, klar ueber Band
                nb2 = np.array([geometrisch(gepflanzt[zieh_tagestreu()])
                                for _ in range(N.NULL_ZIEHUNGEN)])
                if geometrisch(gepflanzt[zus]) > float(
                        np.percentile(nb2, N.NULL_PERZENTIL)):
                    gefunden += 1
            print("           Positivkontrolle: %d von 5 gepflanzten "
                  "Effekten gefunden  %s"
                  % (gefunden,
                     "✔" if gefunden >= 4 else "⛔ der Test ist zu stumpf"))

            # ── 5. DAS KERNSTUECK: bringt die DIFFERENZIERUNG etwas? ──
            #
            # ⭐⭐ Bis hierher ist nur geprueft, ob `q` TRIFFT. Im Betrieb
            # bestimmt die Tabelle aber den HEBEL - und die Frage ist, ob
            # es besser ist, nach Band zu hebeln als ueberall gleich.
            #
            # Gerechnet wird der Kontoertrag je Trade als `kelly_i * r_i`
            # (halbes Kelly, wie `betraege.hebelrechnung` es tut) und
            # daraus der geometrische Ertrag. Die Kontrolle nimmt fuer
            # ALLE Signale denselben Kelly - den Mittelwert. Traegt die
            # Differenzierung nichts, sind beide gleich.
            #
            # ⚠️ Der Kelly kommt aus der KALIBRIERHAELFTE (Falle 1), das
            # Ergebnis aus der Pruefhaelfte.
            kel = np.zeros(n)
            for (lo, hi), (_qe, _be, k_e) in tab.items():
                m = np.isfinite(W) & (W >= lo) & (W < hi)
                kel[m] = max(0.0, k_e) / 2.0          # halbes Kelly
            eff = kel[sig]
            if eff.sum() > 0:
                x = 1.0 + eff * r_all[sig]
                x_g = 1.0 + float(eff.mean()) * r_all[sig]
                if np.all(x > 0) and np.all(x_g > 0):
                    diff = float(np.expm1(np.mean(np.log(x))))
                    gleich = float(np.expm1(np.mean(np.log(x_g))))
                    print("           DIFFERENZIERUNG: nach Band %+.5f %% "
                          "gegen gleicher Hebel %+.5f %% -> %s"
                          % (100 * diff, 100 * gleich,
                             "✔ Band ist besser" if diff > gleich
                             else "⛔ gleicher Hebel ist gleich gut oder besser"))
                else:
                    print("           DIFFERENZIERUNG: Totalverlust moeglich "
                          "- Kelly zu gross")
        print()

    print("=" * 104)
    print("ERGEBNIS: %d von %d Fenstern bestanden" % (bestanden, laeufe))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Die LLM-Stufe ist nicht Teil der Rechnung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
