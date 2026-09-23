# -*- coding: utf-8 -*-
"""IST `funding` EIN ZUSTANDSABHAENGIGER SCHALTER? Hypothese B.

⚠️⚠️⚠️ DIE VORABFESTLEGUNG STEHT IN
`Basisinfos/Vorabfestlegung_Funding_Zustandsschalter_23_09.md` UND WIRD
HIER NICHT NACHVERHANDELT. Sie nennt Recherchestand, die sieben
Zulaessigkeitskriterien fuer einen Zustand, beide Hypothesen, die
Messstufen und - das Entscheidende - was welches Ergebnis BEDEUTET.

## Die Frage

`funding` traegt als Schalter: die Sperre des obersten Rangfuenftels
bringt +0,0234 R, B6 erfuellt. OFFEN ist, ob diese Wirkung vom
MARKTZUSTAND abhaengt - ob der Beitrag also nur dann etwas sagt, wenn der
Markt ueberhitzt ist.

## ⚠️ Warum die ROLLENDE Zustandsdefinition und nicht die absolute

Die absolute Grenze (Tagesmedian ueber der Binance-Standardrate), auf der
die 30.08.-Zahlen stehen, ist nach Kriterium Z3 UNZULAESSIG: ihre letzte
Episode endet am 2024-12-09, sie kommt in den juengsten 21 Monaten NICHT
vor. Eine Messung darauf waere eine Aussage ueber eine vergangene Epoche.

Gewaehlt ist deshalb der ROLLENDE Rang des Tagesmedians in den letzten
250 Tagen. Er erfuellt Z1 (die Sache ist "heiss relativ zum aktuellen
Regime"), Z2 (ein Rang kennt keinen Massepunkt - die absolute Grenze lag
exakt auf 0,0003), Z3 (299 Tage, davon 175 in der ZWEITEN Haelfte) und Z7
(er blickt nur zurueck, kein Look-Ahead).

## ⚠️⚠️ DIE MACHBARKEITSSTUFE LAEUFT ZUERST

Die Lehre aus Vorabfestlegung 4: dort kam die Positivkontrolle NACH dem
Ergebnis, und das Urteil kippte von "Gleichstand" auf "nichts
entschieden". Hier steht sie davor - findet die Anlage auf der duennen
Hoch-Menge (13 Episoden) keinen gepflanzten Effekt, wird die Messung GAR
NICHT durchgefuehrt.

## Der Messstandard gilt vollstaendig

Gemessen wird mit `messnorm.pruefe()` - DER einen Messung, keine
Nachbildung. Sie ruft `messe_regel_wirksamkeit.wirkung()`, dieselbe
Funktion, mit der F-212 gerechnet und reproduziert wurde. Nullpunkt aus
40 Ziehungen, Trennschaerfe gegen denselben Bezug, Pflanzung in die
GEMISCHTE Welt, Blocklaenge `_block(20)` = 60 (nicht 250 wie am 30.08.).

⚠️ NUR LESEND, gegen die Messbasis am Desktop.

    python phase4_funding_zustandsschalter.py
"""
from __future__ import annotations

import statistics as st
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messnorm                                              # noqa: E402

HORIZONT = 20
FENSTER = 250              # Rueckblick fuer den rollenden Rang
HEISS, RUHIG = 0.80, 0.20  # Rangschwellen des Tagesmedians
MACHBAR_BIS = 0.10         # S0: findet die Anlage 0,10 R? (Par. 4)


def lade_je_tag() -> dict:
    """{tag: [{sym, kennzahl, in_r}]} - dasselbe Format wie am 30.08.

    ⚠️ Die Ladung ist NICHT nachgebaut: `messe_eigenschaft_beitrag.lade`
    und `messe_funding_niveau.lade_funding` sind dieselben Funktionen, die
    `pruefe_funding_wirksamkeit.py` benutzt. Nur so ist S1 eine
    Reproduktion und keine neue Messung.
    """
    reihen = B.lade()
    funding = F.lade_funding()
    je_tag: dict = {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f:
            continue
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in f:
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "kennzahl": f[tage[i]],
                 "in_r": float((c[i + HORIZONT] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= 12}


def zustand_je_tag(je_tag: dict) -> dict:
    """Rollender Rang des Tagesmedians in den letzten FENSTER Tagen.

    ⚠️ KEIN LOOK-AHEAD (Z7): das Fenster ist `[i-FENSTER, i)`, der heutige
    Wert selbst gehoert NICHT hinein. Die ersten FENSTER Tage bekommen
    keinen Zustand und fallen aus der Messung - genau wie bei `momentum250`.
    """
    tage = sorted(je_tag)
    med = np.array([st.median([x["kennzahl"] for x in je_tag[t]])
                    for t in tage])
    aus = {}
    for i in range(FENSTER, len(tage)):
        fenster = med[i - FENSTER:i]
        rang = float(np.mean(fenster < med[i]))
        aus[tage[i]] = ("heiss" if rang >= HEISS
                        else "ruhig" if rang <= RUHIG else "mittel")
    return aus


def messe(name: str, teil: dict, rng, hypothesen: int = 1):
    """`messnorm.pruefe` - DIE eine Messung, keine Nachbildung."""
    if len(teil) < messnorm._block(HORIZONT) + 30:
        print("     %-24s ⛔ nur %d Tage - zu wenig fuer ein Band"
              % (name, len(teil)))
        return None
    try:
        return messnorm.pruefe(
            name, teil,
            lage=messnorm.Lage("spot", "einstieg"),
            zielgroesse="bewegung_r", menge="messuniversum",
            frageart="markt", rng=rng, horizont=HORIZONT,
            hypothesen=hypothesen)
    except ValueError as e:                                  # noqa: BLE001
        print("     %-24s ⛔ %s" % (name, e))
        return None


def zeile(name, b, anteil=None):
    if b is None:
        return False
    traegt = b.unten > b.null_oben
    print("     %-22s %+.5f R  [%+.5f .. %+.5f]  Null %+.5f  "
          "%4d Tage %3d Bl.  TS %.4f  %s%s"
          % (name, b.wirkung, b.unten, b.oben, b.null_oben,
             b.n_tage, b.n_bloecke,
             b.trennschaerfe if b.trennschaerfe is not None else float("nan"),
             "✔ TRAEGT" if traegt else "⚠ nicht trennbar",
             "" if anteil is None else "  (%4.1f %% der Tage)" % (100 * anteil)))
    return traegt


def main() -> int:
    print("=" * 112)
    print("FUNDING - IST ES EIN ZUSTANDSABHAENGIGER SCHALTER? (Hypothese B)")
    print("=" * 112)
    print("  Vorabfestlegung: "
          "Basisinfos/Vorabfestlegung_Funding_Zustandsschalter_23_09.md")
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Zustand: rollender Rang des Tagesmedians, Fenster %d Tage, "
          "heiss >= %.2f, ruhig <= %.2f" % (FENSTER, HEISS, RUHIG))

    print("\n  Laden ...")
    je_tag = lade_je_tag()
    zust = zustand_je_tag(je_tag)
    tage = sorted(zust)
    print("  %d Kalendertage mit Zustand, %s bis %s" % (len(tage), tage[0],
                                                        tage[-1]))
    mengen = {z: {t: je_tag[t] for t in tage if zust[t] == z}
              for z in ("heiss", "mittel", "ruhig")}
    for z in ("heiss", "mittel", "ruhig"):
        print("     %-7s %4d Tage (%4.1f %%)"
              % (z, len(mengen[z]), 100.0 * len(mengen[z]) / len(tage)))

    rng = np.random.default_rng(messnorm.SAAT)

    # ---- S0  MACHBARKEIT -------------------------------------------
    # ⚠️⚠️ OHNE ✔ ENDET ES HIER. Die Vorabfestlegung Par. 4 ist
    # ausdruecklich: ein Abbruch ist ein ZULAESSIGER Ausgang.
    print("\n" + "-" * 112)
    print("  S0  MACHBARKEIT - findet die Anlage auf der HEISS-Menge "
          "ueberhaupt etwas?")
    print("-" * 112)
    b0 = messe("S0 heiss", mengen["heiss"], rng)
    if b0 is None:
        print("\n  ⛔ ABBRUCH - kein Band auf der Heiss-Menge. "
              "Die Datenlage reicht nicht (Vorabfestlegung Par. 6, Zeile 1).")
        return 0
    ts = b0.trennschaerfe_in_r
    print("     gepflanzt gefunden ab: %s"
          % ("%.2f R" % ts if ts is not None else "GAR NICHT"))
    print("     %d Bloecke" % b0.n_bloecke)
    if ts is None or ts > MACHBAR_BIS:
        print("\n  ⛔⛔ ABBRUCH NACH VORABFESTLEGUNG PARAGRAF 4.")
        print("     Die Anlage findet auf dieser Menge erst %s - verlangt"
              % ("%.2f R" % ts if ts is not None else "GAR NICHTS"))
        print("     waren hoechstens %.2f R. Die Frage ist mit dieser"
              % MACHBAR_BIS)
        print("     Datenlage NICHT entscheidbar; ein Ergebnis waere in")
        print("     jede Richtung wertlos.")
        print()
        print("     ⚠️ DAS IST KEIN SCHEITERN DER ARBEIT: Hypothese A steht")
        print("     unveraendert (+0,0234 R, B6 erfuellt). `funding` bleibt")
        print("     der belegte Zweistufen-Schalter.")
        print("=" * 112)
        return 0
    print("     ✔ MACHBAR - die Messung wird durchgefuehrt.")

    # ---- S1  REPRODUKTION (R-R11) ----------------------------------
    print("\n" + "-" * 112)
    print("  S1  R-R11 REPRODUKTION - traegt die Regel auf der VOLLEN Menge?")
    print("       (30.08. gemessen: +0,0234 R [+0,0099 .. +0,0381])")
    print("-" * 112)
    b1 = messe("S1 volle Menge", {t: je_tag[t] for t in tage}, rng)
    repro = zeile("volle Menge", b1)
    if not repro:
        print("\n  ⛔ STOPP nach Vorabfestlegung Paragraf 6, Zeile 2:")
        print("     die Registrierung reproduziert NICHT. Dann steht die")
        print("     ganze funding-Registrierung zur Debatte, nicht die Form.")
        print("=" * 112)
        return 0

    # ---- S2/S3  DIE ZUSTAENDE, UND BEIDE HAELFTEN ------------------
    print("\n" + "-" * 112)
    print("  S2  DIE REGELWIRKUNG JE ZUSTAND  (hypothesen=3, Mehrfachtest)")
    print("-" * 112)
    ergebnis = {}
    for z in ("heiss", "mittel", "ruhig"):
        b = messe("S2 %s" % z, mengen[z], rng, hypothesen=3)
        ergebnis[z] = b
        zeile(z, b, len(mengen[z]) / len(tage))

    print("\n  S3  B6 - JEDER ZUSTAND IN BEIDEN HISTORIENHAELFTEN")
    m = len(tage) // 2
    grenze = tage[m]
    b6 = {}
    for z in ("heiss", "mittel", "ruhig"):
        for nm, wahl in (("1.H", lambda t: t < grenze),
                         ("2.H", lambda t: t >= grenze)):
            teil = {t: v for t, v in mengen[z].items() if wahl(t)}
            b = messe("%s %s" % (z, nm), teil, rng, hypothesen=3)
            b6[(z, nm)] = zeile("%-7s %s" % (z, nm), b)

    # ---- S4  B4 - HAEUFIGKEIT MAL WIRKUNG --------------------------
    # ⚠️ OHNE DIESE ZEILE DREHT SICH DIE RANGFOLGE (R-R8 B4): eine grosse
    # Wirkung auf seltenen Tagen kann weniger wert sein als eine kleine
    # auf allen.
    print("\n" + "-" * 112)
    print("  S4  B4 - EFFEKTIV JE SIGNAL  (Haeufigkeit x Wirkung)")
    print("-" * 112)
    print("     %-22s %10s %10s %12s" % ("", "Anteil", "Wirkung", "effektiv"))
    if b1 is not None:
        print("     %-22s %9.1f %% %+9.5f %+11.5f"
              % ("heute (alle Tage)", 100.0, b1.wirkung, b1.wirkung))
    summe = 0.0
    for z in ("heiss", "mittel", "ruhig"):
        b = ergebnis[z]
        if b is None:
            continue
        a = len(mengen[z]) / len(tage)
        summe += a * b.wirkung
        print("     %-22s %9.1f %% %+9.5f %+11.5f"
              % ("nur %s" % z, 100 * a, b.wirkung, a * b.wirkung))
    print("     %-22s %9s  %8s %+11.5f" % ("Summe der Zustaende", "", "", summe))

    # ⚠️⚠️⚠️ DIE SELBSTKONTROLLE UND DIE EIGENTLICHE ANTWORT.
    #
    # Die Summe MUSS die Gesamtwirkung ergeben - die Regelwirkung ist das
    # ueber die Tage gemittelte "mit Regel minus ohne", und an einem Tag
    # ohne Sperre ist sie null. Weicht sie ab, stimmt die Rechnung nicht.
    #
    # Daraus folgt die Antwort auf Hypothese B, und sie ist ARITHMETIK,
    # nicht Statistik: wer NUR im heissen Zustand sperrt, bekommt
    # `Anteil x Wirkung` - und wirft die Wirkung der uebrigen Tage weg.
    # Ein Zustandsschalter kann die unbedingte Regel also nur schlagen,
    # wenn die uebrigen Zustaende NEGATIV wirken. Tun sie das nicht, ist
    # er zwangslaeufig schlechter.
    if b1 is not None:
        print("\n     SELBSTKONTROLLE  Summe %+.5f gegen Gesamt %+.5f  %s"
              % (summe, b1.wirkung,
                 "✔ stimmig" if abs(summe - b1.wirkung) < 1e-4
                 else "⛔ RECHNUNG STIMMT NICHT"))
        nur_heiss = (len(mengen["heiss"]) / len(tage)
                     * (ergebnis["heiss"].wirkung
                        if ergebnis["heiss"] is not None else 0.0))
        print("\n     ⚠️ DIE BETRIEBSFRAGE - unbedingt gegen zustandsabhaengig:")
        print("        unbedingt sperren (heute)      %+.5f R" % b1.wirkung)
        print("        nur im Zustand heiss sperren   %+.5f R" % nur_heiss)
        print("        ➤ %s"
              % ("der Zustandsschalter waere BESSER" if nur_heiss > b1.wirkung
                 else "der Zustandsschalter waere SCHLECHTER - er wirft die "
                      "Wirkung der uebrigen %4.1f %% Tage weg"
                      % (100 * (1 - len(mengen["heiss"]) / len(tage)))))

    # ---- DIE ENTSCHEIDUNG ------------------------------------------
    print("\n" + "=" * 112)
    print("  ENTSCHEIDUNG nach Vorabfestlegung 5, Paragraf 6")
    print("=" * 112)
    bh, br = ergebnis["heiss"], ergebnis["ruhig"]
    getrennt = (bh is not None and br is not None
                and (bh.unten > br.oben or br.unten > bh.oben))
    b6_heiss = b6.get(("heiss", "1.H")) and b6.get(("heiss", "2.H"))
    effektiv_besser = (b1 is not None and summe > b1.wirkung)

    if not getrennt:
        print("     ➤ HYPOTHESE B TRAEGT NICHT - die Baender der Zustaende")
        print("       ueberlappen. `funding` bleibt der Zweistufen-Schalter")
        print("       aus Hypothese A (+0,0234 R, B6 erfuellt).")
        print()
        print("       ⚠️ DAS IST EIN ERGEBNIS, KEIN PATT: die")
        print("       Machbarkeitsstufe S0 ist bestanden, die Anlage haette")
        print("       einen Unterschied dieser Groesse also gefunden.")
    elif not b6_heiss:
        print("     ⛔ B6 VERLETZT - der Zustandsunterschied traegt nicht in")
        print("       beiden Historienhaelften. KEIN UMBAU (wie 2.553).")
        print()
        print("     ⚠️⚠️ ABER B4 IST DIE STAERKERE AUSSAGE, und sie haengt")
        print("       NICHT an B6, weil sie Arithmetik ist: wer nur im")
        print("       heissen Zustand sperrt, bekommt %+.5f R statt %+.5f."
              % (len(mengen["heiss"]) / len(tage)
                 * (ergebnis["heiss"].wirkung
                    if ergebnis["heiss"] is not None else 0.0),
                 b1.wirkung if b1 is not None else float("nan")))
        print("       Der Zustandsschalter waere also selbst dann schlechter,")
        print("       wenn B6 hielte. ➤ DIE UNBEDINGTE SPERRE IST RICHTIG -")
        print("       und das ist ein ERGEBNIS, kein Nullbefund.")
    elif not effektiv_besser:
        print("     ⛔ B4 ENTSCHEIDET DAGEGEN - der Zustandsschalter ist je")
        print("       Signal NICHT besser als die heutige Regel, obwohl der")
        print("       Unterschied belegt ist. KEIN UMBAU.")
    else:
        print("     ✔✔ HYPOTHESE B BELEGT - Zustaende getrennt, B6 erfuellt,")
        print("       effektiv je Signal besser. Bauform: Zweistufen-")
        print("       Schalter A mit zustandsabhaengigem Gewicht.")
        print("       ⚠️ DANACH PFLICHT: R-R9 (Schwelle neu kalibrieren) und")
        print("       eine Betriebspruefung am Notebook.")
    print("=" * 112)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
