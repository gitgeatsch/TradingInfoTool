# -*- coding: utf-8 -*-
"""A2/K-1c — gelten die BEITRAEGE fuer die AKKUMULATION? (10.09.2026)

## Die Frage, und warum der erste Anlauf scheiterte

K-1c hat gefragt, ob die registrierten Beitraege auch fuer
`spot x akkumulation` gelten. **Alle fuenf Kandidaten - einschliesslich
der Kontrolle - lieferten KEIN BEFUND: 6 bis 10 Bloecke gegen 20
geforderte** (2.235).

⚠️⚠️ **Die Ursache ist NICHT das Nullmodell, sondern das BAND.** Bei H90
ist ein Block 3 x 90 = 270 Tage; fuer 20 Bloecke braeuchte es 5.400
Handelstage, rund 22 Jahre. Der Kryptomarkt hat 2.900.

> N-46b hat den Laengs-NULLPUNKT entschieden (Tagesmischung). **Das loest
> A2 nicht** - dort fehlt das Band, nicht der Nullpunkt.

## Der Ausweg: ein PERMUTATIONSTEST statt eines Bootstrap-Bandes

Der Befund vom 28.08. hat bei **H90 auf 505 Reihen** gemessen, ohne
Bloecke - mit dem **zirkulaeren Verschub auf der Kalenderachse**:

| Zelle | Rangvorsprung | Zufall 5-95 % | p | |
|---|---|---|---|---|
| UNTER_SMA | +0,0283 | -0,0124 .. +0,0089 | 0,000 | traegt |
| TIEFPUNKT *(Positivkontrolle)* | +0,4242 | -0,0337 .. +0,0292 | 0,000 | Anlage intakt |
| WOCHENTAG *(Negativkontrolle)* | -0,0008 | ±0,0007 | 0,978 | liegt auf null |
| DCA *(Rechenkontrolle)* | ±0,0000 | — | — | Pflicht |

**Ein Permutationstest braucht keine Bloecke**, weil der Verschub die
Abhaengigkeitsstruktur ERHAELT, statt sie zu zerschneiden. Genau deshalb
funktioniert er bei H90.

⚠️ **Das ist ein Methodenwechsel, kein Parameterwechsel** - und er ist
hier ausdruecklich benannt, nicht stillschweigend vollzogen.

## Die BRUECKE, die dieses Werkzeug baut

`messe_akkumulationsmass` kennt nur Kursreihen; die registrierten
Beitraege sind **Querschnittsraenge je Tag**. Hier werden sie in einen
`zustand` uebersetzt - „ist heute ein guter Kauftag fuer dieses Symbol":

    gut(sym, t)  :=  Querschnittsrang der Kennzahl < 0,20

⚠️ **Richtung:** `marktrang` haelt fest, dass **Fuenftel 0 das gute Ende
ist** - wenig Funding heisst wenig Ueberhitzung, wenig Umschlag heisst
wenig Aufmerksamkeit, tief unter dem Schnitt heisst Rueckkehr. Das
unterste Fuenftel ist damit das Gegenstueck zu `UNTER_SMA`.

⚠️⚠️ Das ist NICHT dieselbe Regel wie bei `bewegung_r`. Dort lautet sie
„sperre das OBERSTE Fuenftel" (`GRENZE = 0,80`); hier wird das UNTERSTE
als Kaufzustand gepruef. Beides ist dieselbe Richtung, nur einmal als
Sperre und einmal als Anlass formuliert.

## Die Aufloesung - eigens fuer diese Zielgroesse bestimmt

⚠️ Die Grenze aus A9 (0,08 R bei hoher Beharrlichkeit) gilt hier NICHT:
sie wurde auf `bewegung_r` in **R** gemessen. `verbilligung` ist ein
**Perzentilrang** mit Basisrate exakt 0,500 - andere Skala.

**Die Aufloesung dieses Tests ist die Breite seiner eigenen
Nullverteilung**, und die wird mitgedruckt. Am 28.08. lag sie bei
-0,0124 .. +0,0089; Effekte darunter sind nicht nachweisbar.

## Die Nutzervorgabe, unter der das steht (10.09.)

> *„Bei der Akkumulation koennen wir mit Unschaerfen am ehesten leben."*

⚠️ Fachlich stimmig: die Akkumulation hat **keinen Stop** und kauft
**gestaffelt** - ein einzelner falscher Tag kostet dort wenig, weil die
Staffelung mittelt. Das rechtfertigt ein breiteres Band und geschichtete
statt direkter Evidenz. **Es rechtfertigt nicht, auf den Nachweis zu
verzichten** - die Kontrollen laufen unveraendert.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    schnitt        traegt - er IST das Akkumulationsmass (2.155)
    funding        offen - ein Querschnittsrang beantwortet die
                   Laengsfrage „war es ein guter Kauftag" moeglicherweise
                   gar nicht
    turnover       offen, zusaetzlich duenne Abdeckung (66 von 536)
    oi_aenderung   offen
    zufall         darf NICHT tragen
    TIEFPUNKT      muss tragen, sonst gilt der Lauf nicht

    python n101_a2_akkumulation.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_akkumulationsmass as AM                          # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messe_regel_wirksamkeit as W                           # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import zusatzquellen               # noqa: E402

H = 90
VORLAUF = AM.VORLAUF
VERSCHUEBE = 400
SAAT = 20260910
GUT = 0.20               # das unterste Fuenftel des Querschnittsrangs
KANDIDATEN = ("schnitt", "funding", "turnover", "oi_aenderung", "zufall")


def lade_mit_daten(db: str, min_tage: int, assetklasse: str = "krypto"):
    """Wie `AM.lade_reihen`, gibt aber die DATUMSLISTE je Symbol mit.

    ## ⚠️⚠️ Warum das noetig ist

    Der Kaufzustand kommt aus `K.baue` und ist nach DATUM verschluesselt;
    die Kursreihe ist nach INDEX adressiert. Der erste Entwurf hat die
    Tagesliste aus `je` genommen und angenommen, sie sei dieselbe Folge
    wie die der Kursreihe.

    **Das ist sie nicht** - `K.baue` schneidet den Horizont ab und kann
    spaeter beginnen. Die Maske waere dann um einen unbekannten Betrag
    verschoben gewesen, und zwar STILL: die Zahlen haetten plausibel
    ausgesehen.

    Hier wird die Zuordnung an der Quelle gebildet, aus derselben
    Abfrage wie die Kurse.
    """
    import sqlite3
    from collections import defaultdict
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    kurse, daten = defaultdict(list), defaultdict(list)
    for sym, tag, kurs in c.execute(
            "SELECT symbol, date, close FROM price_history_ohlc "
            "WHERE close IS NOT NULL AND close > 0 AND assetklasse = ? "
            "AND currency = 'USD' ORDER BY symbol, date", (assetklasse,)):
        kurse[sym].append(float(kurs))
        daten[sym].append(str(tag)[:10])
    c.close()
    achse = sorted({t for ts in daten.values() for t in ts})
    pos = {t: i for i, t in enumerate(achse)}
    reihen, start, tage = {}, {}, {}
    for sym, v in kurse.items():
        if len(v) < min_tage:
            continue
        # ⚠️ Nur lueckenlose Reihen - sonst ist der Indexabstand kein
        # Tagesabstand, und der Verschub verschoebe um etwas anderes.
        erster, letzter = pos[daten[sym][0]], pos[daten[sym][-1]]
        if letzter - erster + 1 != len(v):
            continue
        reihen[sym] = np.asarray(v, dtype=float)
        start[sym] = erster
        tage[sym] = daten[sym]
    return reihen, start, len(achse), tage


def gut_je_symbol(je_tag: dict) -> dict:
    """{sym: {tag: True}} - war dieses Symbol heute im untersten Fuenftel?

    ⚠️ Der Rang entsteht ueber den vollen Tagesquerschnitt, wie
    `marktrang` in der Produktion. Erst danach wird je Symbol abgelegt.
    """
    aus: dict = {}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        r = W.rang(kz)
        for i, z in enumerate(zeilen):
            if r[i] < GUT:
                aus.setdefault(z["sym"], set()).add(tag)
    return aus


def messe_zustand(reihen, start, achse, zustand_je_sym, tage_index, rng):
    """Rangvorsprung des Zustands und seine Verschubverteilung.

    ⚠️ Baugleich zu `messe_akkumulationsmass.messe`, aber der Zustand
    kommt von aussen statt aus einer Kursregel. EIN Satz Verschuebe in
    Kalendertagen, **fuer jedes Symbol derselbe** - der dokumentierte
    Fehler vom 28.08. war, den eigenen Startpunkt hinzuzuaddieren.
    """
    beob, n_sym, treffer, tage_ges = 0.0, 0, 0, 0
    verschoben = np.zeros(VERSCHUEBE)
    versatz = rng.integers(H, max(H + 1, achse - H), size=VERSCHUEBE)

    for sym in sorted(reihen):
        c = reihen[sym]
        v = AM.verbilligung(c, H)
        if len(v) <= VORLAUF + 60:
            continue
        v = v[VORLAUF:]
        idx = tage_index.get(sym)
        if idx is None:
            continue
        gut = zustand_je_sym.get(sym)
        if not gut:
            continue
        # Bool-Maske auf derselben Achse wie `v`.
        m = np.array([(idx[VORLAUF + i] in gut) if VORLAUF + i < len(idx)
                      else False for i in range(len(v))], bool)
        if m.sum() < 5 or m.sum() == len(m):
            continue
        r = AM.rang(v)
        beob += float(r[m].mean()) - 0.5
        n_sym += 1
        treffer += int(m.sum())
        tage_ges += len(m)
        # ⚠️⚠️ ZIRKULAERER VERSCHUB - UM d, FUER JEDES SYMBOL GLEICH.
        #
        # Der erste Entwurf dieses Skripts rechnete `(d - s0) % len(m)`,
        # zog also den Startpunkt des Symbols ab. Das ist derselbe Fehler
        # wie am 28.08., nur mit umgekehrtem Vorzeichen: JEDE
        # symbolabhaengige Verschiebung hebt die Gleichzeitigkeit des
        # Marktes auf und macht die Nullverteilung zu eng.
        #
        # ⚠️ Bei lueckenlosen Tagesreihen IST ein Verschub um d Indizes
        # ein Verschub um d Kalendertage. `messe_akkumulationsmass` haelt
        # es genauso: `np.roll(m, int(d) % len(m))`.
        for j, d in enumerate(versatz):
            verschoben[j] += float(
                r[np.roll(m, int(d) % len(m))].mean()) - 0.5
    if not n_sym:
        return None
    return {"wert": beob / n_sym,
            "null": verschoben / n_sym,
            "symbole": n_sym,
            "quote": (100.0 * treffer / tage_ges) if tage_ges else 0.0}


def urteil(e) -> tuple:
    """(p, unten, oben, wort) aus der Verschubverteilung.

    ## ⚠️⚠️ DREI Urteile, nicht zwei

    Der erste Entwurf gab nur `traegt = wert > oben` zurueck und schrieb
    alles andere als „traegt nicht". **Das ist zu grob** - und es ist
    dieselbe Verwechslung wie Fehler 4 vom 08.09.: eine Eigenschaft
    gelesen statt eines Urteils.

    Im Lauf lagen `funding` (-0,0230) und `oi_aenderung` (-0,0178) WEIT
    UNTER dem Nullband, mit p = 0,000. Das ist kein Nullbefund, sondern
    ein **umgekehrter** Effekt: ihr „gutes" Fuenftel ist systematisch der
    SCHLECHTERE Kauftag.

        TRAEGT       ueber dem Band  - das gute Fuenftel ist besser
        UMGEKEHRT    unter dem Band  - es ist SCHLECHTER
        traegt nicht im Band          - kein Unterschied
    """
    u = float(np.percentile(e["null"], 5))
    o = float(np.percentile(e["null"], 95))
    p = float((np.abs(e["null"]) >= abs(e["wert"])).mean())
    if e["wert"] > o:
        return p, u, o, "⚠️ TRAEGT"
    if e["wert"] < u:
        return p, u, o, "⚠️⚠️ UMGEKEHRT"
    return p, u, o, "traegt nicht"


def main() -> int:
    t0 = time.time()
    reihen, start, achse, tage_je_sym = lade_mit_daten(
        AM.DB, VORLAUF + H + 60)
    zus = zusatzquellen()
    messreihen = B.lade()

    print("=" * 108)
    print("A2/K-1c — gelten die BEITRAEGE fuer die AKKUMULATION?")
    print("=" * 108)
    print("  %s" % messmenge.zeile())
    print("  H%d · Verbilligung als Perzentilrang (Basisrate exakt 0,500) "
          "· %d Verschuebe" % (H, VERSCHUEBE))
    print("  ⚠️ PERMUTATIONSTEST statt Bootstrap-Band - bei H90 gibt es "
          "keine 20 Bloecke (2.235).")
    print("  ⚠️ Kaufzustand = unterstes Fuenftel des Querschnittsrangs "
          "(Fuenftel 0 ist das gute Ende).")
    print("  ⚠️⚠️ Nutzervorgabe 10.09.: bei der Akkumulation sind "
          "Unschaerfen am ehesten tragbar -")
    print("     das erlaubt ein breiteres Band, nicht den Verzicht auf "
          "die Kontrollen.")
    print("  Reihen: %d" % len(reihen))

    # ---- Die Kontrollen aus dem Bestandswerkzeug -------------------------
    print()
    print("  DIE KONTROLLEN (aus `messe_akkumulationsmass`)")
    print("     %-12s %11s %22s %8s  %s"
          % ("Zustand", "Vorsprung", "Zufall 5-95 %", "p", "Urteil"))
    for name in ("TIEFPUNKT", "WOCHENTAG"):
        rng = np.random.default_rng(SAAT)
        e = AM.messe(reihen, start, achse, name, H, rng)
        if not e:
            print("     %-12s nicht messbar" % name)
            continue
        print("     %-12s %+11.4f [%+.4f .. %+.4f] %8.3f  %s"
              % (name, e["vorsprung"], e["null_p05"], e["null_p95"],
                 e["p"],
                 "⚠️ TRAEGT" if e["vorsprung"] > e["null_p95"]
                 else "traegt nicht"), flush=True)

    # ---- Die Kandidaten --------------------------------------------------
    print()
    print("  DIE KANDIDATEN")
    print("     %-14s %11s %22s %8s %8s %8s  %s"
          % ("Kandidat", "Vorsprung", "Zufall 5-95 %", "p", "Symbole",
             "Quote", "Urteil"))
    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(messreihen, kand, zus.get(kand), horizont=20)
        except Exception as exc:                              # noqa: BLE001
            print("     %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        gut = gut_je_symbol(je)
        rng = np.random.default_rng(SAAT)
        # ⚠️ Die Datumsliste kommt aus DERSELBEN Abfrage wie die Kurse -
        # nicht aus `je`. Siehe `lade_mit_daten`.
        e = messe_zustand(reihen, start, achse, gut, tage_je_sym, rng)
        if e is None:
            print("     %-14s nicht messbar" % kand)
            continue
        p, u, o, wort = urteil(e)
        erg[kand] = (e, p, u, o, wort)
        print("     %-14s %+11.4f [%+.4f .. %+.4f] %8.3f %8d %7.1f %%  %s"
              % (kand, e["wert"], u, o, p, e["symbole"], e["quote"], wort),
              flush=True)

    # ---- Abnahme ---------------------------------------------------------
    print()
    print("=" * 108)
    print("DIE ABNAHME")
    print("=" * 108)
    zf = erg.get("zufall")
    if zf and zf[4] != "traegt nicht":
        print("  ⚠️⚠️⚠️ DIE KONTROLLE `zufall` ist NICHT stumm (%s) - der "
              "Lauf gilt NICHT." % zf[4])
    elif zf:
        print("  ✔ `zufall` traegt nicht (%+.4f, p %.3f)"
              % (zf[0]["wert"], zf[1]))
    umgekehrt = [k for k, v in erg.items()
                 if k != "zufall" and v[4].endswith("UMGEKEHRT")]
    if umgekehrt:
        print("  ⚠️⚠️ UMGEKEHRT (das ,gute' Fuenftel ist der SCHLECHTERE "
              "Kauftag): %s" % ", ".join(umgekehrt))
        print("     Das ist KEIN Nullbefund - die Richtung ist belegt, "
              "nur andersherum als erwartet.")
    if erg:
        breite = np.mean([e[3] - e[2] for e in erg.values()])
        print("  ⚠️ AUFLOESUNG dieser Zielgroesse: die Nullverteilung ist "
              "im Mittel %.4f breit" % breite)
        print("     (5-95 %%). Effekte darunter sind mit diesem Test "
              "nicht nachweisbar.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
