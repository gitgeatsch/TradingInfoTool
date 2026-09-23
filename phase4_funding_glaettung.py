# -*- coding: utf-8 -*-
"""KOSTET DIE GLAETTUNG WIRKUNG? Vorabfestlegung 6.

⚠️⚠️⚠️ DIE VORABFESTLEGUNG STEHT IN
`Basisinfos/Vorabfestlegung_Funding_Glaettung_23_09.md` UND WIRD HIER
NICHT NACHVERHANDELT.

## Die Frage

Nutzerkritik: *"ein Schalter ist per Definition eine Falle, da minimale
Bewegungen alles oder nichts bedeuten"*. Gemessen wurde daraufhin die
URSACHE - und sie liegt NICHT an der Kante:

    ueber die Rangkante 0,80        17,58 % Wechsel je Tag
    ueber die absolute Grenze       18,21 %  - MEHR, nicht weniger
    Rangwechsel ohne eigene Aenderung   nur 18,2 % aller Wechsel

⚠️ 82 Prozent sind ECHTE eigene Bewegungen: die EINGANGSGROESSE schwankt.
Keine Grenzverschiebung hilft, eine Glaettung sehr wohl (17,5 -> 5,9 % bei
sieben Tagen).

## Warum Glaettung fachlich richtig ist und keine Ordnung behauptet

Funding wird ALLE ACHT STUNDEN abgerechnet. Ein Tageswert ist ein
MOMENTwert; die oekonomisch gemeinte Groesse - "zahlt die Long-Seite hier
dauerhaft drauf?" - ist ein NIVEAU ueber Tage. Die Glaettung korrigiert
also die GROESSE, nicht das Urteil. Sie ist damit vereinbar mit allen
fuenf Messungen, die die Fuenferleiter widerlegt haben.

⚠️⚠️ ZUGLEICH IST SIE EIN VERDACHT AUF EINEN B1-VERSTOSS (R-R8, "richtige
FORM"): die heutige Groesse nimmt den Momentwert. Die Durchsicht vom
30.08. hat bei `funding` nur die RICHTUNG korrigiert (Niveau statt
Veraenderung), nicht die ZEITBASIS.

## ⚠️ KEIN LOOK-AHEAD

Gemittelt wird ueber das Fenster [t-n+1 .. t] - der heutige Wert ist der
JUENGSTE, nie ein zukuenftiger. Ueber KALENDERTAGE, nicht ueber
Listeneintraege, damit Luecken das Fenster nicht heimlich verlaengern.

⚠️ NUR LESEND, gegen die Messbasis am Desktop.

    python phase4_funding_glaettung.py
"""
from __future__ import annotations

import datetime as dt
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messnorm                                              # noqa: E402

HORIZONT = 20
FENSTER = (1, 3, 7, 14)
MACHBAR_BIS = 0.10
REPRO_SOLL = 0.0234        # 30.08., muss von n=1 reproduziert werden


def glaette(f: dict, n: int) -> dict:
    """Mittel ueber die KALENDERTAGE [t-n+1 .. t] je Symbol.

    ⚠️ Ueber Kalendertage, nicht ueber Listeneintraege: haette ein Symbol
    eine Luecke, wuerde ein Eintragsfenster heimlich weiter zurueckgreifen
    und fuer verschiedene Symbole verschieden lange Zeitraeume mitteln.
    """
    if n <= 1:
        return f
    tage = sorted(f)
    d = [dt.date.fromisoformat(t) for t in tage]
    v = np.array([f[t] for t in tage], float)
    aus, j = {}, 0
    for i, heute in enumerate(d):
        ab = heute - dt.timedelta(days=n - 1)
        while d[j] < ab:
            j += 1
        aus[tage[i]] = float(v[j:i + 1].mean())
    return aus


def lade(n: int) -> dict:
    """{tag: [{sym, kennzahl, in_r}]} mit ueber n Tage geglaettetem Funding.

    ⚠️ Die Ladung ist NICHT nachgebaut - `messe_eigenschaft_beitrag.lade`
    und `messe_funding_niveau.lade_funding` sind dieselben Funktionen, die
    `pruefe_funding_wirksamkeit.py` benutzt. Nur so ist n=1 eine
    Reproduktion und keine neue Messung.
    """
    reihen = B.lade()
    funding = F.lade_funding()
    je_tag: dict = {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f:
            continue
        g = glaette(f, n)
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in g:
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "kennzahl": g[tage[i]],
                 "in_r": float((c[i + HORIZONT] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= 12}


def kantenwechsel(je_tag: dict) -> float:
    """Anteil der Symbol-Tagespaare, die ueber die Rangkante 0,80 springen.

    ⚠️ DAS IST DIE ZWEITE ZIELGROESSE (Vorabfestlegung Par. 5) - gerechnet,
    nicht geschaetzt. Die Nutzerkritik zielt genau auf diese Zahl.
    """
    tage = sorted(je_tag)
    wechsel = paare = 0
    for i in range(1, len(tage)):
        vor, jetzt = je_tag[tage[i - 1]], je_tag[tage[i]]
        ra = np.argsort(np.argsort([x["kennzahl"] for x in vor])) \
            / max(len(vor) - 1, 1)
        rb = np.argsort(np.argsort([x["kennzahl"] for x in jetzt])) \
            / max(len(jetzt) - 1, 1)
        A = {x["sym"]: r for x, r in zip(vor, ra)}
        Bb = {x["sym"]: r for x, r in zip(jetzt, rb)}
        for s in set(A) & set(Bb):
            paare += 1
            wechsel += (A[s] >= 0.80) != (Bb[s] >= 0.80)
    return wechsel / max(paare, 1)


def messe(name, je_tag, rng, hypothesen=1):
    try:
        return messnorm.pruefe(
            name, je_tag, lage=messnorm.Lage("spot", "einstieg"),
            zielgroesse="bewegung_r", menge="messuniversum",
            frageart="markt", rng=rng, horizont=HORIZONT,
            hypothesen=hypothesen)
    except ValueError as e:                                  # noqa: BLE001
        print("     %-18s ⛔ %s" % (name, e))
        return None


def zeile(name, b, extra=""):
    if b is None:
        return False
    traegt = b.unten > b.null_oben
    print("     %-18s %+.5f R  [%+.5f .. %+.5f]  Null %+.5f  %4d Tage "
          "%3d Bl.  TS %.4f  %s%s"
          % (name, b.wirkung, b.unten, b.oben, b.null_oben, b.n_tage,
             b.n_bloecke,
             b.trennschaerfe if b.trennschaerfe is not None else float("nan"),
             "✔ TRAEGT" if traegt else "⚠ nicht trennbar", extra))
    return traegt


def main() -> int:
    print("=" * 116)
    print("FUNDING - KOSTET DIE GLAETTUNG WIRKUNG? (Vorabfestlegung 6)")
    print("=" * 116)
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Fenster: %s Tage · Glaettung ueber KALENDERTAGE, nur Rueckblick"
          % (FENSTER,))

    daten, kanten = {}, {}
    for n in FENSTER:
        print("\n  Laden n=%d ..." % n)
        daten[n] = lade(n)
        kanten[n] = kantenwechsel(daten[n])
        print("     %d Tage, Kantenwechsel %5.2f %%"
              % (len(daten[n]), 100 * kanten[n]))

    rng = np.random.default_rng(messnorm.SAAT)

    # ---- S0  MACHBARKEIT -------------------------------------------
    print("\n" + "-" * 116)
    print("  S0  MACHBARKEIT - findet die Anlage auf JEDER Kandidatenmenge "
          "gepflanzte <= %.2f R?" % MACHBAR_BIS)
    print("-" * 116)
    befunde, machbar = {}, True
    for n in FENSTER:
        b = messe("n=%d" % n, daten[n], rng, hypothesen=len(FENSTER))
        befunde[n] = b
        ts = b.trennschaerfe_in_r if b is not None else None
        ok = ts is not None and ts <= MACHBAR_BIS
        machbar = machbar and ok
        print("     n=%-3d  gepflanzt gefunden ab %s   %s"
              % (n, ("%.2f R" % ts) if ts is not None else "GAR NICHT",
                 "✔" if ok else "⛔"))
    if not machbar:
        print("\n  ⛔⛔ ABBRUCH nach Vorabfestlegung Paragraf 6, Zeile 1.")
        print("     Nicht jede Kandidatenmenge ist aufloesbar - ein")
        print("     Vergleich waere nicht deutbar.")
        print("=" * 116)
        return 0
    print("     ✔ MACHBAR auf allen Fenstern.")

    # ---- S1  R-R11 --------------------------------------------------
    print("\n" + "-" * 116)
    print("  S1  R-R11 - reproduziert n=1 den 30.08.-Wert %+.4f R?" % REPRO_SOLL)
    print("-" * 116)
    repro = zeile("n=1 (heute)", befunde[1])
    if not repro:
        print("\n  ⛔ STOPP nach Paragraf 6, Zeile 2: die Registrierung")
        print("     reproduziert nicht. Dann steht sie zur Debatte, nicht")
        print("     die Glaettung.")
        print("=" * 116)
        return 0

    # ---- S2  DIE FENSTER -------------------------------------------
    print("\n" + "-" * 116)
    print("  S2  DIE WIRKUNG JE FENSTER  (hypothesen=%d)" % len(FENSTER))
    print("-" * 116)
    for n in FENSTER:
        zeile("n=%d" % n, befunde[n],
              "   Kante %5.2f %%" % (100 * kanten[n]))

    # ---- S3  B6 ----------------------------------------------------
    print("\n  S3  B6 - JEDES FENSTER IN BEIDEN HISTORIENHAELFTEN")
    b6 = {}
    for n in FENSTER:
        tage = sorted(daten[n])
        m = len(tage) // 2
        for nm, teil in (("1.H", {t: daten[n][t] for t in tage[:m]}),
                         ("2.H", {t: daten[n][t] for t in tage[m:]})):
            b6[(n, nm)] = zeile("n=%-2d %s" % (n, nm),
                                messe("n=%d %s" % (n, nm), teil, rng,
                                      hypothesen=len(FENSTER)))

    # ---- S4  WIRKUNG GEGEN STABILITAET -----------------------------
    print("\n" + "-" * 116)
    print("  S4  WIRKUNG GEGEN KANTENSTABILITAET")
    print("-" * 116)
    print("     %-8s %12s %14s %12s %10s"
          % ("Fenster", "Wirkung", "Band unten", "Kante", "B6"))
    for n in FENSTER:
        b = befunde[n]
        if b is None:
            continue
        beide = b6.get((n, "1.H")) and b6.get((n, "2.H"))
        print("     n=%-6d %+11.5f %+13.5f %11.2f %% %10s"
              % (n, b.wirkung, b.unten, 100 * kanten[n],
                 "✔" if beide else "⛔"))

    # ---- DIE ENTSCHEIDUNG ------------------------------------------
    # ⚠️ Zwei Fenster gelten als UNTERSCHIEDLICH, wenn das Band des einen
    # den Punktwert des anderen ausschliesst. Ueberlappende Baender sagen
    # NICHTS ueber ihren Unterschied (Memory `ueberlappende-baender`) -
    # deshalb wird hier bewusst nur die GROBE Frage gestellt: ist ein
    # Fenster BELEGT besser oder BELEGT schlechter als n=1?
    print("\n" + "=" * 116)
    print("  ENTSCHEIDUNG nach Vorabfestlegung 6, Paragraf 6")
    print("=" * 116)
    eins = befunde[1]
    besser = [n for n in FENSTER if n > 1 and befunde[n] is not None
              and befunde[n].unten > eins.oben]
    schlechter = [n for n in FENSTER if n > 1 and befunde[n] is not None
                  and befunde[n].oben < eins.unten]
    if besser:
        gut = [n for n in besser if b6.get((n, "1.H")) and b6.get((n, "2.H"))]
        if gut:
            print("     ✔✔ UMBAU AUF n=%d - belegt besser als n=1, B6 erfuellt."
                  % max(gut))
            print("       Danach PFLICHT: R-R9 (Schwelle) + Betriebspruefung.")
        else:
            print("     ⛔ besser, aber B6 verletzt - KEIN UMBAU.")
    elif schlechter:
        print("     ⛔ n=%s ist BELEGT SCHLECHTER als n=1." % schlechter)
        print("       Der Effekt steckt im MOMENTwert. Kein Umbau - und die")
        print("       Kantenkritik bleibt dann offen und unloesbar.")
    else:
        print("     ➤ GLEICHSTAND - kein Fenster ist belegt besser ODER")
        print("       schlechter als n=1. Die Glaettung KOSTET also nichts.")
        print()
        print("       ⚠️⚠️ DAS IST KEIN BELEG FUER DIE GLAETTUNG, SONDERN EINE")
        print("       ERLAUBNIS. Was fuer sie spricht, ist die KANTE:")
        for n in FENSTER:
            print("          n=%-3d %5.2f %% Wechsel" % (n, 100 * kanten[n]))
        print("       Die Wahl eines Fensters ist damit eine KONSTRUKTIVE")
        print("       Entscheidung (Robustheit), keine gemessene Ueber-")
        print("       legenheit - und wird genau so berichtet.")
    print("=" * 116)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
