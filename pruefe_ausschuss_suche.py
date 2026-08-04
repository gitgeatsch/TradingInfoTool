"""Pruefstand fuer die Ausschuss-Suche (Phase 1.1 Teil B, 2026-08-04).

Vermisst das Suchverfahren aus agent/krypto/ausschuss_suche.py an
synthetischen Welten mit BEKANNTER Wahrheit, bevor es echte Daten sieht.

Vier Akzeptanzkriterien (Zielgroessen_und_Erfolgsmasse.md 7.2):
  1. H0-Falschtrefferquote <= 5 %
  2. grober Effekt (+2,0 R) wird in >= 95 % gefunden
  3. die Symbolblockung wirkt nachweislich - naive Auswertung derselben
     geklumpten Daten muss deutlich mehr Fehlalarme erzeugen
  4. der Generator trifft die realen Randverteilungen

Dazu die VORWAERTSRECHNUNGEN nach stehender Nutzer-Vorgabe ("was wir nicht an
Daten haben, rechnen wir vorwaerts und simulieren"): welche Effektgroesse ist
mit dem vorhandenen n nachweisbar, und welches n braeuchte +0,3 R? Geringe
Trennschaerfe ist damit ein Zielwert, kein Abbruchgrund.

Lauf: python pruefe_ausschuss_suche.py [--schnell]
"""
from __future__ import annotations

import sys
import time

import numpy as np

from agent.krypto.ausschuss_suche import ausschuss_suche

SCHNELL = "--schnell" in sys.argv

# --- Gemessene Struktur der echten Population (Export 04.08.) ---------------
# hebel: 86 aufgeloest real + 327 aufgeloest Schatten = 413 Faelle
# aus 21 Symbolen, stark ungleich verteilt (LINK 12, KAIA 11, INJ 8, ...)
N_MERKMALE = 43                       # gemeinsamer Kern Hebel n Spot
SYMBOL_GROESSEN = [58, 52, 40, 34, 33, 28, 26, 23, 20, 18,
                   16, 14, 12, 10, 8, 6, 5, 4, 3, 2, 1]   # Summe 413
CRV_MEDIAN = 2.6
BASIS_TREFFERQUOTE = 0.26             # ergibt EW nahe dem gemessenen -0,10 R
SYMBOL_STREUUNG = 0.08                # Symbol-Effekt auf die Trefferquote
# Intraklassen-Korrelation der Merkmale: Anteil der Merkmalsvarianz, der
# ZWISCHEN den Symbolen liegt. GEMESSEN an den 413 aufgeloesten Hebel-Signalen
# (Median ueber 14 numerisierbare Merkmale), nicht geschaetzt - der erste
# Entwurf stand auf 0,6 und haette die Trennschaerfe-Rechnung verfaelscht.
#
#   confidence_pct 0,282 | forecast_bull 0,229 | hebel_vorschlag 0,261
#   halte_kriterium_bucket 0,413 | trade_thesis_typ 0,433 | richtung 0,368
#   top_grund_1_kategorie 0,031  -> Median 0,301
#
# WICHTIG, aus derselben Messung: entry_usd_von / stop_loss_usd_von /
# take_profit_usd_von haben ICC 0,998-1,000. Absolute Preisfelder SIND
# praktisch Symbol-Kennungen; ein Schnitt darauf findet "Symbol X ist gut",
# verkleidet als Merkmalsregel. Sie duerfen der Suche nur in RELATIVER Form
# (stop_rel, CRV) vorgelegt werden - siehe MERKMALE_AUSSCHLUSS in
# agent/krypto/ausschuss_suche.py.
ICC_MERKMALE = 0.30

LAEUFE = 60 if SCHNELL else 150
NULL_ZIEHUNGEN = 120 if SCHNELL else 250


def erzeuge_welt(rng: np.random.Generator, effekt_r: float = 0.0,
                 n_skalierung: float = 1.0, icc: float | None = None,
                 symbol_streuung: float | None = None):
    """Eine synthetische Signalmenge mit der gemessenen Struktur.

    `effekt_r` = 0 erzeugt Welt H0: das Ergebnis haengt von KEINEM Merkmal ab.
    Groesser 0 pflanzt eine bekannte Regel ein (Merkmal 7 >= 0,6), deren
    Teilmenge den Erwartungswert um `effekt_r` anhebt.

    Wichtig fuer die Aussagekraft: der Symbol-Effekt wirkt auf die
    Trefferquote, nicht auf einzelne Faelle. Dadurch entsteht die
    Innen-Korrelation, die die Blockung ueberhaupt erst noetig macht -
    ohne sie waere der Pruefstand zu freundlich.
    """
    groessen = [max(1, int(round(g * n_skalierung))) for g in SYMBOL_GROESSEN]
    symbole = np.concatenate([np.full(g, f"SYM{i:02d}") for i, g in enumerate(groessen)])
    n = len(symbole)

    _, cluster = np.unique(symbole, return_inverse=True)
    n_cluster = cluster.max() + 1

    # Merkmale: teils unabhaengig, teils korreliert - reale Merkmale sind es
    # auch (confidence_pct und forecast_bull_prob_pct laufen zusammen).
    basis = rng.normal(size=(n, 8))
    ladung = rng.normal(size=(8, N_MERKMALE)) * 0.5
    zeilenanteil = basis @ ladung + rng.normal(size=(n, N_MERKMALE))
    zeilenanteil /= zeilenanteil.std(0)

    # SYMBOL-ANTEIL IN DEN MERKMALEN - ohne ihn ist der Pruefstand wertlos.
    # Die erste Fassung zog X unabhaengig vom Symbol; dann kann ein
    # Merkmalsschnitt nie mit einem Symbol zusammenfallen, und die Klumpung
    # wird gar nicht geprueft. In echten Daten hat jedes Symbol
    # charakteristische Konfidenz-, Regime- und Zonenwerte - genau deshalb
    # war am 04.08. naiv p=0,039 und symbolgeblockt p=0,194.
    #
    # Die Mischung ist so gewaehlt, dass die Intraklassen-Korrelation EXAKT
    # ICC_MERKMALE ergibt (Varianzanteile sqrt(icc) / sqrt(1-icc)) - nicht
    # ueber einen Skalierungsfaktor geschaetzt.
    icc_wert = ICC_MERKMALE if icc is None else icc
    symbol_niveau = rng.normal(size=(n_cluster, N_MERKMALE))
    X = (np.sqrt(icc_wert) * symbol_niveau[cluster]
         + np.sqrt(1.0 - icc_wert) * zeilenanteil)
    X = (X - X.mean(0)) / X.std(0)
    # Merkmal 7 auf [0,1] bringen - dort wird die Regel eingepflanzt. Bewusst
    # OHNE Symbolanteil: die eingepflanzte Regel soll eine echte Merkmals-
    # regel sein, keine getarnte Symbolauswahl.
    X[:, 7] = rng.uniform(size=n)

    # Symbol-Effekt auf die Trefferquote
    streuung = SYMBOL_STREUUNG if symbol_streuung is None else symbol_streuung
    versatz = rng.normal(0.0, streuung, size=n_cluster)
    q = np.clip(BASIS_TREFFERQUOTE + versatz[cluster], 0.02, 0.9)

    if effekt_r > 0:
        # EW = q*CRV - (1-q) -> dEW/dq = CRV + 1
        maske = X[:, 7] >= 0.6
        q = q.copy()
        q[maske] = np.clip(q[maske] + effekt_r / (CRV_MEDIAN + 1.0), 0.02, 0.95)

    treffer = rng.random(n) < q
    y = np.where(treffer, CRV_MEDIAN, -1.0)
    return X, y, symbole


def lauf(rng, effekt_r, n_skalierung=1.0, ziehungen=None, **welt):
    X, y, sym = erzeuge_welt(rng, effekt_r, n_skalierung, **welt)
    return ausschuss_suche(X, y, sym, [f"m{i:02d}" for i in range(N_MERKMALE)],
                           null_ziehungen=ziehungen or NULL_ZIEHUNGEN,
                           seed=int(rng.integers(1, 2**31)))


def quote(rng, effekt_r, laeufe, alpha=0.05, n_skalierung=1.0, **welt):
    """Anteil der Laeufe, in denen das Verfahren einen Fund meldet."""
    treffer = 0
    for _ in range(laeufe):
        e = lauf(rng, effekt_r, n_skalierung, **welt)
        if e.p_wert is not None and e.p_wert <= alpha:
            treffer += 1
    return treffer / laeufe


def naive_quote(rng, laeufe, alpha=0.05, **welt):
    """Dasselbe, aber mit ZEILENWEISER Vertauschung statt Symbolblockung.

    Zeigt, was die Blockung leistet: dieselben geklumpten Daten, nur die
    Nullhypothese anders erzeugt."""
    from agent.krypto.ausschuss_suche import MIN_ANTEIL, _bester_schnitt

    treffer = 0
    for _ in range(laeufe):
        X, y, sym = erzeuge_welt(rng, 0.0, **welt)
        namen = [f"m{i:02d}" for i in range(N_MERKMALE)]
        min_n = max(3, int(np.ceil(MIN_ANTEIL * len(y))))
        idx = np.argsort(X, axis=0, kind="stable")
        beob, _k = _bester_schnitt(X, idx, y, namen, min_n)
        null = np.empty(NULL_ZIEHUNGEN)
        for i in range(NULL_ZIEHUNGEN):
            null[i], _ = _bester_schnitt(X, idx, rng.permutation(y), namen, min_n)
        p = (np.sum(null >= beob) + 1) / (NULL_ZIEHUNGEN + 1)
        if p <= alpha:
            treffer += 1
    return treffer / laeufe


def main() -> int:
    start = time.time()
    rng = np.random.default_rng(20260804)
    fehler: list[str] = []
    print("=" * 78)
    print(f"PRUEFSTAND AUSSCHUSS-SUCHE   {LAEUFE} Laeufe, "
          f"{NULL_ZIEHUNGEN} Nullziehungen{'  [SCHNELL]' if SCHNELL else ''}")
    print("=" * 78)

    # --- 4. Generator zuerst: stimmt die Welt ueberhaupt? ------------------
    X, y, sym = erzeuge_welt(rng, 0.0)
    print(f"\n4) GENERATOR   n={len(y)}  Symbole={len(np.unique(sym))}  "
          f"Merkmale={X.shape[1]}")
    print(f"   EW = {y.mean():+.3f} R   Trefferquote = {(y > 0).mean()*100:.1f} %"
          f"   groesstes Symbol = {max(SYMBOL_GROESSEN)/len(y)*100:.0f} % der Faelle")
    ok4 = (-0.30 < y.mean() < 0.05) and 0.15 < (y > 0).mean() < 0.40
    print(f"   {'OK  ' if ok4 else 'FEHL'}  im Bereich der echten Population "
          f"(EW -0,10 R, Trefferquote ~26 %)")
    if not ok4:
        fehler.append("Generator trifft die reale Verteilung nicht")

    # --- 1. Falschtrefferquote --------------------------------------------
    print(f"\n1) H0-FALSCHTREFFERQUOTE  (kein Merkmal wirkt)")
    fp = quote(rng, 0.0, LAEUFE)
    ok1 = fp <= 0.10          # Toleranz fuer die endliche Laufzahl
    print(f"   gemessen {fp*100:5.1f} %   Soll <= 5 % (Toleranz 10 % bei "
          f"{LAEUFE} Laeufen)")
    print(f"   {'OK  ' if ok1 else 'FEHL'}  Mehrfachtestung ist eingepreist")
    if not ok1:
        fehler.append(f"Falschtrefferquote {fp*100:.0f} % zu hoch")

    # --- 3. Wirkt die Blockung? -------------------------------------------
    #
    # ERSTE FASSUNG WAR FALSCH KONSTRUIERT: sie verglich beide Verfahren bei
    # der GEMESSENEN Klumpung (ICC 0,30). Dort liegen beide nahe am Sollwert
    # (4,0 % gegen 7,3 % bei 50 bzw. 150 Laeufen) - der Vergleich mass
    # Rauschen statt des Mechanismus und schlug entsprechend zufaellig fehl.
    #
    # Ein Mechanismus zeigt sich dort, wo er gebraucht wird. Deshalb eine
    # Welt mit STARKER Klumpung: Merkmale fast symbolkonstant (ICC 0,85) und
    # deutlicher Symbol-Effekt auf die Trefferquote. Genau diese
    # Konstellation liess am 04.08. naiv p=0,039 und geblockt p=0,194
    # entstehen.
    print(f"\n3) WIRKUNG DER SYMBOLBLOCKUNG  (Testwelt mit starker Klumpung)")
    stark = {"icc": 0.85, "symbol_streuung": 0.22}
    print(f"   ICC 0,85 statt gemessener 0,30, Symbol-Effekt 0,22 statt 0,08 -")
    print(f"   hier MUSS die naive Null versagen, sonst prueft der Test nichts.")
    n3 = max(40, LAEUFE // 3)
    fp_naiv = naive_quote(rng, n3, **stark)
    fp_block = quote(rng, 0.0, n3, **stark)
    print(f"   zeilenweise Vertauschung: {fp_naiv*100:5.1f} % Fehlalarme")
    print(f"   Block-Umsortierung:       {fp_block*100:5.1f} %")
    # Bewertet wird die WIRKUNG, nicht die Beseitigung: bei ICC 0,85 sind die
    # Merkmale fast symbolkonstant, ein Merkmalsschnitt IST dann ein
    # Symbolschnitt. Kein Permutationsverfahren kann das vollstaendig
    # auffangen - die Blockung muss die Aufblaehung aber deutlich senken.
    ok3 = fp_naiv > 0.5 and fp_block <= fp_naiv / 2
    print(f"   {'OK  ' if ok3 else 'FEHL'}  naive Null versagt ({fp_naiv*100:.0f} %), "
          f"Blockung mindestens halbiert")
    print(f"   (bei GEMESSENER Klumpung ICC 0,30: geblockt {fp*100:.1f} %)")
    if not ok3:
        fehler.append(f"Blockung wirkt nicht: naiv {fp_naiv*100:.0f} %, "
                      f"geblockt {fp_block*100:.0f} %")

    # --- 5. Bis zu welcher Klumpung traegt das Verfahren? ------------------
    # Aus Kriterium 3 folgt eine Betriebsgrenze, die nicht geraten werden
    # darf: ab welcher ICC steigt die Falschtrefferquote ueber das
    # Vertretbare? Das Ergebnis wird zur Aufnahmeschwelle fuer echte
    # Merkmale (ICC_OBERGRENZE in ausschuss_suche.py).
    print(f"\n5) BETRIEBSGRENZE  (ab welcher Symbolabhaengigkeit kippt es?)")
    print(f"   {'ICC':>6s} {'Fehlalarme':>12s}")
    grenze = None
    for icc_wert in (0.30, 0.45, 0.60, 0.75):
        r = quote(rng, 0.0, max(30, LAEUFE // 4), icc=icc_wert)
        marke = ""
        if r > 0.10 and grenze is None:
            grenze = icc_wert
            marke = "  <-- ueber 10 %"
        print(f"   {icc_wert:6.2f} {r*100:11.0f} %{marke}")
    if grenze:
        print(f"   -> Merkmale mit ICC >= {grenze:.2f} sind fuer diese Suche "
              f"NICHT zulaessig")
    else:
        print(f"   -> bis ICC 0,75 tragfaehig")

    # --- 2. Grober Effekt --------------------------------------------------
    print(f"\n2) FUNKTIONSPRUEFUNG  (grober Effekt +2,0 R eingepflanzt)")
    p_grob = quote(rng, 2.0, max(30, LAEUFE // 3))
    ok2 = p_grob >= 0.95
    print(f"   gefunden in {p_grob*100:5.1f} %   Soll >= 95 %")
    print(f"   {'OK  ' if ok2 else 'FEHL'}  Verfahren findet, was da ist")
    if not ok2:
        fehler.append(f"grober Effekt nur zu {p_grob*100:.0f} % gefunden")

    # --- VORWAERTSRECHNUNG 1: nachweisbare Effektgroesse --------------------
    print(f"\nVORWAERTS 1) Welche Effektgroesse ist mit n={len(y)} nachweisbar?")
    print(f"   {'Effekt':>10s} {'Trennschaerfe':>15s}")
    kurve = []
    for e in (0.2, 0.3, 0.5, 0.8, 1.2):
        p = quote(rng, e, max(25, LAEUFE // 4))
        kurve.append((e, p))
        marke = "  <-- 80 %" if p >= 0.8 else ""
        print(f"   {e:9.1f} R {p*100:14.0f} %{marke}")
    nachweisbar = next((e for e, p in kurve if p >= 0.8), None)
    if nachweisbar:
        print(f"   -> ab etwa {nachweisbar:.1f} R zuverlaessig nachweisbar")
    else:
        print(f"   -> selbst {kurve[-1][0]:.1f} R erreicht keine 80 % "
              f"(beste: {max(p for _, p in kurve)*100:.0f} %)")

    # --- VORWAERTSRECHNUNG 2: benoetigtes n fuer +0,3 R --------------------
    print(f"\nVORWAERTS 2) Welches n braeuchte der realistische Effekt +0,3 R?")
    print(f"   {'n':>7s} {'Trennschaerfe':>15s}")
    benoetigt = None
    for faktor in (1, 2, 4, 8):
        n_erw = int(sum(SYMBOL_GROESSEN) * faktor)
        p = quote(rng, 0.3, max(20, LAEUFE // 5), n_skalierung=faktor)
        marke = "  <-- 80 %" if p >= 0.8 else ""
        print(f"   {n_erw:7d} {p*100:14.0f} %{marke}")
        if p >= 0.8 and benoetigt is None:
            benoetigt = n_erw
    if benoetigt:
        print(f"   -> ab rund {benoetigt} aufgeloesten Faellen entscheidbar "
              f"(heute {sum(SYMBOL_GROESSEN)})")
    else:
        print(f"   -> auch die achtfache Menge reicht nicht - der Effekt ist "
              f"zu klein fuer diese Struktur")

    print()
    print("=" * 78)
    dauer = time.time() - start
    if fehler:
        print(f"FEHLGESCHLAGEN nach {dauer:.0f} s: {fehler}")
        return 1
    print(f"Alle vier Akzeptanzkriterien bestanden ({dauer:.0f} s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
