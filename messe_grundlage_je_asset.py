# -*- coding: utf-8 -*-
"""Traegt die Achse ABSOLUT - und traegt sie JE ASSET? Befund 2.647.

**27.09.2026.** Zwei Nutzervorgaben treffen hier zusammen.

═══════════════════════════════════════════════════════════════════════
 WOZU - DIE ZWEITE FRAGE IST DIE WICHTIGERE
═══════════════════════════════════════════════════════════════════════

    1.  *"wenn du falsch beginnst, sind die Messungen danach auch
        wertlos"* - 2.626 hat nur TAGESTREU gemessen, also innerhalb
        eines Tages. Traegt die Achse auch ABSOLUT, gegen den Markt?

    2.  ⚠️⚠️ *"nicht den Markt alleine messen, sondern die Bewertung
        muss auf das Asset gehen"* (27.09.) - und das ist die
        registrierte stehende Vorgabe `feedback_nicht_den_markt_messen_
        sondern_beitraege_je_asset`.

⛔⛔ DIE FALLE, DIE FRAGE 2 STELLT: "+1,2568 % gegen Markt +0,0150 %"
ist ein GEPOOLTER Vergleich. Wenn die scharfen Lagen bevorzugt in
wenigen volatilen Symbolen auftreten, misst diese Zahl die
SYMBOLAUSWAHL und nicht die LAGE - und ein Beitrag, der nur Symbole
sortiert, ist nach Regel 3 (kein Asset-Rang beim Hebel) unbrauchbar.

⭐ DER AUSWEG IST EIN ANDERER BEZUG, NICHT EINE ANDERE ZAHL: jeder
Anker wird gegen den Durchschnitt SEINES EIGENEN Symbols gehalten. Was
danach uebrig bleibt, ist der Beitrag der Lage - symbolneutral.

═══════════════════════════════════════════════════════════════════════
 DIE SECHS PRUEFUNGEN (die fuenf der Bilanz plus die Assetfrage)
═══════════════════════════════════════════════════════════════════════

    1  Nullwelt      tagestreu, 40 Ziehungen, 90. Perzentil
    2  Zeitstabil    je Kalenderjahr gegen den Markt DESSELBEN Jahres
    3  Weglassprobe  ohne je ein Jahr
    4  Mehrfachtest  Bestes-von-fuenf-Band ueber alle Schwellen
    5  Ebene         B - Erfolgsmessung, kein Rueckfluss in die Bewertung
    6  JE ASSET      Lift gegen das eigene Symbol · Anteil positiver
                     Symbole · Konzentration der Auswahl

⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).
⚠️ NUR LESEN.  python messe_grundlage_je_asset.py [--symbole N]
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
from messe_hebel_neudimension import (EMA_L, VORLAUF,           # noqa: E402
                                      trailing_mit_ausloeser)

H = 24                       # Messfenster aus 2.642
WEITE, AUSL, ABST = 1.0, 1.5, 0.5     # Geometrie aus 2.628
SCHWELLEN = (-1.0, -1.2881, -1.5, -1.65, -1.8)
ZIEHUNGEN = 40               # Messstandard
SAAT = 20260927
MIN_TREFFER = 30             # je Symbol, sonst ist der Lift Rauschen
MIN_JAHR = 100               # Anker je Jahr, sonst ist es keine Aussage
MIN_SYMBOLE = 20             # Symbole mit genug Treffern, sonst dito


def lade():
    """-> (W, ERTRAG, tag, jahr, SI, namen) ueber alle Symbole ausser BTC.

    ⚠️⚠️ TAG UND JAHR KOMMEN AUS DEM ZEITSTEMPEL, NICHT AUS EINEM INDEX.
    Die erste Fassung bildete sie als `G // 24` und `G // (24*365)` aus
    dem Rang der Stunde in der globalen Stundenliste. Das ist zweimal
    falsch:

        1.  Die Reihe beginnt am **01.12.2021**. "Jahr 0" lief damit von
            Dezember 2021 bis November 2022 - die Beschriftung sagte
            "2022" und meinte etwas anderes.
        2.  Bei einem TEILLAUF (`--symbole N`) enthaelt die Stundenliste
            weniger Stunden, der Index staucht sich, und die Grenzen
            verschieben sich noch einmal anders.

    ➤ Deshalb wich der Teillauf vom vollen Lauf ab (5 von 5 gegen 4 von
      5 Jahren) - nicht in den Daten, sondern in der Beschriftung. Genau
      die registrierte Regel *kleine Laeufe taeuschen*.
    """
    kurse = lade_kurse(None if "--symbole" not in sys.argv
                       else int(sys.argv[sys.argv.index("--symbole") + 1]))
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle)
    sid = {s: i for i, s in enumerate(sl)}
    # echte Kalendergroessen je globaler Stunde - "2026-09-24 15:00"
    # ⚠️ `return_inverse` gibt eine DICHTE, AUFSTEIGENDE Tagesnummer -
    # die Nullwelt zerlegt die Reihe nach Tagesbloecken und braucht die
    # Sortierbarkeit.
    _dat = np.array([x[:10] for x in sl])
    _, tag_je_i = np.unique(_dat, return_inverse=True)
    jahr_je_i = np.array([int(x[:4]) for x in sl], np.int64)
    G, W, E, SI, namen = [], [], [], [], []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        _r, kp, _d = trailing_mit_ausloeser(h, l, cc, atr, WEITE, AUSL,
                                            ABST, H)
        gu = (np.isfinite(atr) & (atr > 0) & np.isfinite(w) & np.isfinite(kp))
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        i = len(namen)
        namen.append(sym)
        G.append(gi[s2])
        W.append(w[s2])
        E.append(kp[s2] * 100.0)
        SI.append(np.full(len(s2), i, np.int64))
    G = np.concatenate(G)
    return (np.concatenate(W), np.concatenate(E), tag_je_i[G],
            jahr_je_i[G], np.concatenate(SI), namen)


def nullband(W, E, tag, schwelle, rng):
    """90. Perzentil aus TAGESTREU gezogenen Nullwelten (Messstandard).

    ⚠️ Tagestreu heisst: die Ertraege werden INNERHALB jedes Tages
    gemischt. Damit bleibt die Marktphase erhalten und nur die Zuordnung
    Lage->Ertrag zerfaellt - genau die Nullhypothese, die hier gilt.
    """
    m = W <= schwelle
    if not m.any():
        return np.nan
    o = np.argsort(tag, kind="stable")
    ts, es, ms = tag[o], E[o], m[o]
    gr = np.flatnonzero(np.diff(ts)) + 1
    bloecke = np.split(np.arange(len(ts)), gr)
    aus = []
    for _ in range(ZIEHUNGEN):
        s = 0.0
        k = 0
        for b in bloecke:
            z = int(ms[b].sum())
            if not z:
                continue
            s += float(es[rng.choice(b, size=z, replace=False)].sum())
            k += z
        aus.append(s / max(k, 1))
    return float(np.percentile(aus, 90))


def main() -> int:
    print("=" * 108)
    print("DIE GRUNDLAGE: traegt die Achse ABSOLUT - und JE ASSET?")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  H%d · Trailing %.1f/%.1f/%.1f ATR (2.628) · Zielgroesse "
          "Kursprozent" % (H, WEITE, AUSL, ABST))
    print("  ⚠️ Ebene B - Erfolgsmessung. Kein Rueckfluss in die "
          "Bewertung (2.641)")
    print("  ⚠️ Ohne Gebuehren und Finanzierung (Regel 2)")
    print()

    W, E, tag, jahr, SI, namen = lade()
    markt = float(E.mean())
    print("  %d Anker · %d Tage · %d Symbole · Markt %+.4f %%"
          % (len(W), len(np.unique(tag)), len(namen), markt), flush=True)
    print()
    rng = np.random.default_rng(SAAT)

    # ══ 1 + 4: NULLWELT UND MEHRFACHTESTEN ═══════════════════════════
    print("=" * 108)
    print("1 + 4. NULLWELT (tagestreu) UND MEHRFACHTESTEN ueber %d "
          "Schwellen" % len(SCHWELLEN))
    print("  ⚠️ Das Band(%d) ist das SCHAERFSTE der %d Einzelbaender - so "
          "zaehlt" % (len(SCHWELLEN), len(SCHWELLEN)))
    print("     jede Schwelle gegen die Tatsache, dass mehrere getestet "
          "wurden.")
    print()
    zeilen, baender = [], []
    for s in SCHWELLEN:
        m = W <= s
        b = nullband(W, E, tag, s, rng)
        zeilen.append((s, int(m.sum()), float(E[m].mean()), b))
        baender.append(b)
    band = float(np.nanmax(baender))
    print("  %-10s %8s %12s %12s %12s  %s"
          % ("Schwelle", "Anker", "Ertrag %", "Nullband", "Band(%d)"
             % len(SCHWELLEN), "Urteil"))
    ok1 = True
    for s, k, e, b in zeilen:
        gut = e > band
        ok1 &= gut
        print("  %-10.4f %8d %+12.4f %12.4f %12.4f  %s"
              % (s, k, e, b, band, "✔" if gut else "⛔"))
    print("  ➤ %s" % ("alle %d Schwellen ueber dem Band" % len(SCHWELLEN)
                      if ok1 else "⛔ mindestens eine faellt"))

    # ══ 2 + 3: ZEITSTABILITAET UND WEGLASSPROBE ══════════════════════
    ref = -1.2881
    m = W <= ref
    js = np.unique(jahr)
    print()
    print("=" * 108)
    print("2. ZEITSTABILITAET (Schwelle %.4f)" % ref)
    print("  ⚠️ Jedes Jahr gegen den Markt DESSELBEN Jahres - sonst "
          "vergleicht man")
    print("     die Marktphase mit und nicht die Lage.")
    print()
    # ⚠️⚠️ EIN JAHR MIT DREI ANKERN IST KEIN BESTANDENES JAHR. Die erste
    # Fassung zaehlte 2021 (3 Anker - die Reihe beginnt am 01.12.2021)
    # als vollen Treffer und meldete "6 von 6". Duenne Jahre werden
    # AUSGEWIESEN, aber nicht gezaehlt.
    tr = ges = 0
    for j in js:
        jm = jahr == j
        k = int((jm & m).sum())
        if not k:
            continue
        a, b = float(E[jm & m].mean()), float(E[jm].mean())
        duenn = k < MIN_JAHR
        if not duenn:
            ges += 1
            tr += a > b
        print("  Jahr %d  %8d Anker  Auswahl %+9.4f  Markt %+9.4f  %s"
              % (int(j), k, a, b,
                 "zu duenn (<%d), zaehlt nicht" % MIN_JAHR if duenn
                 else ("✔" if a > b else "⛔")))
    print("  ➤ %d von %d Jahren ueber Markt (nur Jahre mit mindestens "
          "%d Ankern)" % (tr, ges, MIN_JAHR))

    print()
    print("=" * 108)
    print("3. WEGLASSPROBE - haelt der Befund ohne je ein Jahr?")
    print()
    wl = 0
    for j in list(js) + [None]:
        keep = np.ones(len(W), bool) if j is None else (jahr != j)
        a = float(E[keep & m].mean())
        b = float(E[keep].mean())
        wl += a > b
        print("  %-14s Auswahl %+9.4f  Markt %+9.4f  %s"
              % ("voll" if j is None else "ohne %d" % int(j), a, b,
                 "✔" if a > b else "⛔"))
    print("  ➤ %d von %d ueber Markt" % (wl, len(js) + 1))

    # ══ 6: DIE ASSETFRAGE ════════════════════════════════════════════
    print()
    print("=" * 108)
    print("6. ⚠️⚠️ JE ASSET - misst die Achse die LAGE oder die "
          "SYMBOLAUSWAHL?")
    print("  Nutzervorgabe 27.09.: *nicht den Markt alleine messen, "
          "sondern die")
    print("  Bewertung muss auf das Asset gehen*")
    print()
    print("  ⭐ Der Bezug ist hier das EIGENE SYMBOL: Lift = Ertrag der "
          "Auswahl")
    print("     in Symbol s MINUS Ertrag aller Anker in Symbol s. Was "
          "davon")
    print("     uebrig bleibt, kann keine Symbolauswahl sein.")
    print()
    print("  %-10s %12s %12s %10s %10s %8s  %s"
          % ("Schwelle", "Symbole", "davon >=%d" % MIN_TREFFER,
             "Lift %", "positiv", "Konz.", "Urteil"))
    ok6 = True
    for s in SCHWELLEN:
        ms = W <= s
        lifte, gew = [], []
        anteile = []
        for i in range(len(namen)):
            si = SI == i
            t = si & ms
            k = int(t.sum())
            if k:
                anteile.append(k)
            if k < MIN_TREFFER:
                continue
            lifte.append(float(E[t].mean()) - float(E[si].mean()))
            gew.append(k)
        if not lifte:
            print("  %-10.4f  zu duenn" % s)
            continue
        lifte = np.array(lifte)
        gew = np.array(gew, float)
        # gewichtet, damit ein Symbol mit 40 Treffern nicht so zaehlt
        # wie eines mit 4.000
        lift = float((lifte * gew).sum() / gew.sum())
        pos = 100.0 * float((lifte > 0).mean())
        # Konzentration: Anteil der Auswahl in den staerksten 10 Symbolen
        an = np.sort(np.array(anteile, float))[::-1]
        konz = 100.0 * float(an[:10].sum() / an.sum())
        # ⚠️⚠️ EINE QUOTE AUS EINEM SYMBOL IST KEINE QUOTE. Bei -1,8 hat
        # nur 1 von 115 Symbolen genug Treffer; "100 % positiv" waere
        # dort eine Scheingenauigkeit - dieselbe Regel wie bei den
        # duennen Jahren oben.
        duenn = len(lifte) < MIN_SYMBOLE
        gut = lift > 0 and pos >= 60.0
        if not duenn:
            ok6 &= gut
        print("  %-10.4f %12d %12d %+10.4f %9.1f%% %7.1f%%  %s"
              % (s, len(anteile), len(lifte), lift, pos, konz,
                 "zu wenige Symbole (<%d), zaehlt nicht" % MIN_SYMBOLE
                 if duenn else ("✔" if gut else "⛔")))
    print()
    print("  ⚠️ Konz. = Anteil der Auswahl in den 10 haeufigsten Symbolen.")
    print("     Bei %d Symbolen waeren rund %.0f%% gleichverteilt."
          % (len(namen), 1000.0 / max(len(namen), 1)))
    print("  ➤ %s" % ("die Lage traegt INNERHALB der Symbole - der Befund "
                      "ist kein Asset-Rang" if ok6 else
                      "⛔ der Lift verschwindet gegen das eigene Symbol"))

    print()
    print("=" * 108)
    print("GESAMT: %s" % ("✔ alle sechs Pruefungen" if
                          (ok1 and ges and tr == ges and wl == len(js) + 1
                           and ok6) else "⛔ mindestens eine faellt"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
