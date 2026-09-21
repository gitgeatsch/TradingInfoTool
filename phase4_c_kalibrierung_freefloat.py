# -*- coding: utf-8 -*-
"""PHASE 4 · PUNKT C - TRAEGT `turnover` AUF DEM FREIEN UMLAUF?

⚠️ Der Nenner von `turnover`. Bisher Coin Metrics `SplyCur` = die
GESAMTAUSGABE auf dem Ledger (2.500-splycur-ist-gesamtausgabe), 61
frische Symbole, im Bestand 5 von 26. Neu: CoinGecko Free Float,
Marktkapitalisierung / Preis, 365 Tage - rund 400 Symbole.

## ⚠️⚠️ WAS HIER GEPRUEFT WIRD - UND WAS DIE FALLE WAERE

Die naheliegende Messung waere: *neue Groesse messen, mit der
registrierten Tabelle vergleichen, fertig.* Das waere falsch. Zwischen
alt und neu haben sich **zwei** Dinge geaendert:

    1 DIE GROESSE   Gesamtausgabe  ->  freier Umlauf
    2 DIE MENGE     61 Symbole     ->  rund 400

Ein anderes Ergebnis liesse sich beiden zuschreiben, und R-R11 verlangt
ausdruecklich: *wer die Basis aendert und etwas anderes bekommt, hat
nichts widerlegt - er hat etwas anderes gemessen.*

## Deshalb DREI Arme, vorab benannt

    ALT       `SplyCur`,    nur die Symbole, die BEIDE Quellen haben
    NEU       Free Float,   DIESELBEN Symbole
    NEU-VOLL  Free Float,   alle, die sie hat

ALT gegen NEU trennt die GROESSE. NEU gegen NEU-VOLL trennt die MENGE.
Ohne diese Trennung ist jede Differenz uninterpretierbar.

## ⚠️ WAS DIESE MESSUNG NICHT KANN - vor dem Lauf gesagt

Das Fenster ist **365 Tage**. Die registrierte Beitragstabelle ist auf
der langen Historie entstanden. Faellt der ALT-Arm hier durch, ist das
**kein Widerruf** der registrierten Tabelle, sondern die Aussage
*„in einem Jahr ist er nicht nachweisbar"*. Genau deshalb laeuft er
ueberhaupt mit: er ist der **Massstab fuer die Aussagekraft des
Fensters**, nicht der Angeklagte.

⚠️⚠️ `_block(H) = max(15, 3 x H)` - NACHGESEHEN, nicht gerechnet. Bei
H2 und H3 bindet der BODEN 15, nicht `3 x H`: alle drei Horizonte
brauchen dieselben **300 Ankertage**, H2 keinen Tag weniger als H5. Ein
kurzer Horizont kauft hier also keine Datenlage. 365 Kalendertage minus
Horizont reichen knapp - mit rund 60 Tagen Luft, nicht mit Reserve. H20
braucht 1.200 und ist ausgeschlossen; das Werkzeug lehnt alles ueber H5
ab, statt es still zu rechnen.

## Zielgroesse

    bewegung_r   HAUPTZELLE - die registrierte Tabelle steht darauf,
                 und R-R11 verlangt den Vergleich auf DERSELBEN Frage
    barriere     zweite Zeile, ausgewiesen - das ist die Groesse, an
                 der der HEBEL haengt (2b)

    python phase4_c_kalibrierung_freefloat.py
    python phase4_c_kalibrierung_freefloat.py --horizonte 2,3,5 \
           --zielgroesse bewegung_r,barriere --menge-db data/umlaufmenge_cg.db
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import k1c_hebel_barriere as K1                          # noqa: E402
import messe_bewertungskennzahl as MB                    # noqa: E402
import messe_eigenschaft_beitrag as B                    # noqa: E402
import messe_kandidaten_als_regel as K                   # noqa: E402
import hole_umlaufmenge_cg as HU                        # noqa: E402
import messmenge                                          # noqa: E402
import messnorm as N                                      # noqa: E402
import messnorm_auswahl as MA                            # noqa: E402
import phase3_stufen as ST                                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250        # noqa: E402

HORIZONTE = (2, 3, 5)
ZIELHOEHE = 2.0
SAAT = 20260921
MENGE_DB = "data/umlaufmenge_cg.db"
ALT_DB = "data/onchain_historie.db"
# ⚠️ Nur ANKER ab hier. Das Fenster der neuen Quelle ist ein Jahr; alles
# davor hat keinen Nenner und faellt in `baue` ohnehin heraus. Der
# ausdrueckliche Schnitt macht es sichtbar statt still.
_SPEICHER: dict = {}


def _arg(args, flagge, vorgabe):
    return args[args.index(flagge) + 1] if flagge in args else vorgabe


def menge_neu(db: str, spitzen_raus: bool = True) -> tuple:
    """Free Float aus dem Vollabruf - nur Symbole mit Urteil `ok`.

    ⚠️⚠️ `spitzen_raus` wirft die gemessenen TAGESARTEFAKTE der Quelle
    aus (2.502-mengenspitzen): an vier Kalendertagen meldet CoinGecko
    fuer 22 bis 39 Symbole gleichzeitig eine exakt runde Zahl und am
    naechsten Tag wieder den alten Wert. Eine Umlaufmenge tut das
    nicht. AUSWERFEN, nicht ersetzen - ein interpolierter Wert waere
    eine Erfindung.

    Mit `--spitzen nein` laeuft die ungefilterte Fassung; so ist der
    Unterschied messbar statt behauptet.
    """
    if not os.path.exists(db):
        raise SystemExit("%s fehlt - erst `hole_umlaufmenge_cg.py` laufen "
                         "lassen" % db)
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    gut = {r[0].upper() for r in c.execute(
        "SELECT symbol FROM abruf_symbol WHERE urteil = 'ok'")}
    roh: dict = {}
    for sym, tag, wert in c.execute(
            "SELECT symbol, datum, wert FROM umlaufmenge WHERE wert > 0 "
            " ORDER BY symbol, datum"):
        s = str(sym).upper()
        if s in gut:
            roh.setdefault(s, []).append((str(tag)[:10], float(wert)))
    c.close()
    aus, weg, ges = {}, 0, 0
    for s, reihe in roh.items():
        ges += len(reihe)
        # ⚠️ DIESELBE Funktion, die der Abruf benutzt - keine Kopie.
        raus = HU.entferne_spitzen([w for _t, w in reihe]) \
            if spitzen_raus else set()
        weg += len(raus)
        aus[s] = {t: w for i, (t, w) in enumerate(reihe) if i not in raus}
    return aus, weg, ges


def _barrieren(reihen: dict, H: int):
    """Ungeloeste zaehlen als verfehlt - das ist der QUOTE-Kanal, `q`."""
    if H not in _SPEICHER:
        _SPEICHER[H] = {s: K1.barriere_je_reihe(v, H, ZIELHOEHE, 0.0)
                        for s, v in reihen.items()}
    return _SPEICHER[H]


def auf_barriere(je_tag: dict, je_sym: dict, ab: str):
    """Wie 2b: dieselbe Mechanik, Mindestbesetzung 12."""
    neu, drin, gesamt = {}, 0, 0
    for tag, zeilen in je_tag.items():
        if str(tag)[:10] < ab:
            continue
        z = []
        for x in zeilen:
            gesamt += 1
            b = (je_sym.get(x["sym"]) or {}).get(tag)
            if b is None:
                continue
            drin += 1
            z.append({"sym": x["sym"], "kennzahl": x["kennzahl"],
                      "in_r": float(b)})
        if len(z) >= 12:
            neu[tag] = z
    return neu, (drin / gesamt if gesamt else 0.0)


def beschneiden(je_tag: dict, erlaubt: set, ab: str):
    """Anker auf eine Symbolmenge und ein Fenster einschraenken.

    ⚠️⚠️ DAS IST DER KERN DES VERGLEICHS. Ein Rang ist ein Perzentil -
    wer die Menge aendert, aendert jeden Wert darin
    (`grundgesamtheit-ist-keine-stellschraube`). ALT und NEU muessen
    deshalb auf BUCHSTAEBLICH denselben Ankertagen und denselben
    Symbolen stehen, sonst vergleicht man zwei Grundgesamtheiten und
    nennt es einen Groessenvergleich.
    """
    neu = {}
    for tag, zeilen in je_tag.items():
        if str(tag)[:10] < ab:
            continue
        z = zeilen if erlaubt is None else [
            x for x in zeilen if x["sym"].upper() in erlaubt]
        if len(z) >= 12:
            neu[tag] = z
    return neu


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:24]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "2,3,5").split(","))
    ziele = tuple(_arg(args, "--zielgroesse",
                       "bewegung_r,barriere").split(","))
    db = _arg(args, "--menge-db", MENGE_DB)
    saat = int(_arg(args, "--saat", str(SAAT)))
    # ⚠ Vorgabe leer = je Arm nach Datenlage. Mit --feste-menge 20%
    # laufen ALLE Arme auf demselben Auswahlanteil, und erst dann ist
    # die Differenz zwischen ihnen die Groesse bzw. die Menge allein.
    fest_menge = _arg(args, "--feste-menge", "")
    # ⚠⚠ DIE SAATPROBE ERREICHTE NUR DEN BOOTSTRAP (21.09.2026).
    # `--saat` geht in das `rng`, mit dem `urteil_tage` zieht. Die 40
    # NULLWELTEN werden in `messnorm.pruefe` dagegen mit der
    # MODULKONSTANTE gemischt (`default_rng(SAAT + z)`, Zeile 757) - eine
    # Saatprobe, die nur `--saat` dreht, laesst den halben Zufall
    # unberuehrt und sieht dadurch stabiler aus, als die Lage ist.
    #
    # ⚠ NICHT GEAENDERT wird die Norm: ein fester Nullbezug ist eine
    # sinnvolle Setzung (dieselbe Nullwelt fuer jede Messung macht
    # Urteile untereinander vergleichbar). Erreichbar GEMACHT wird er,
    # damit die Empfindlichkeit MESSBAR ist statt unbekannt.
    if "--nullsaat" in args:
        N.SAAT = int(_arg(args, "--nullsaat", str(N.SAAT)))
    for h in horizonte:
        if h > 5:
            print("  ⚠️ H%d abgelehnt: %d Ankertage noetig, 365 vorhanden"
                  % (h, 20 * N._block(h)))
            return 2

    t0 = time.time()
    print("=" * 112)
    print("PHASE 4 · PUNKT C - KALIBRIERUNG VON `turnover` AUF DEM FREIEN "
          "UMLAUF")
    print("=" * 112)
    print("  " + N.standardzeile())
    print("  " + messmenge.zeile())

    spitzen = _arg(args, "--spitzen", "ja") == "ja"
    neu, weg, ges = menge_neu(db, spitzen)
    alt = MB.reihe(ALT_DB, "splycur")
    tage_neu = sorted({t for d in neu.values() for t in d})
    ab = tage_neu[0] if tage_neu else "2025-01-01"
    gemeinsam = set(neu) & set(alt)
    print()
    print("  QUELLEN")
    print("    NEU  Free Float (CoinGecko) : %4d Symbole · %s bis %s"
          % (len(neu), ab, tage_neu[-1] if tage_neu else "-"))
    print("         Tagesartefakte der Quelle: %s (%d von %d Punkten = "
          "%.2f %%, 2.502-mengenspitzen)"
          % ("AUSGEWORFEN" if spitzen else "⚠ DRIN GELASSEN "
             "(--spitzen nein)", weg, ges, 100.0 * weg / ges if ges else 0))
    print("    ALT  SplyCur  (Coin Metrics): %4d Symbole" % len(alt))
    print("    gemeinsam (der faire Vergleich): %d Symbole" % len(gemeinsam))
    if len(gemeinsam) < 12:
        print("  ⚠️ unter 12 gemeinsamen Symbolen ist kein Querschnitt "
              "moeglich - der ALT-Arm entfaellt")
    print()
    print("  ⚠️ Fenster %s bis %s. Der ALT-Arm ist hier der MASSSTAB FUER "
          "DAS FENSTER," % (ab, tage_neu[-1] if tage_neu else "-"))
    print("     nicht der Angeklagte: faellt er durch, sagt das etwas ueber "
          "365 Tage,")
    print("     nicht ueber die registrierte Tabelle (R-R11).")
    zellen = len(horizonte) * len(ziele) * 3
    print("  ⚠️ %d Zellen - familienweiter Fehlalarm rund %.0f %%. Geurteilt "
          "wird nach FORM" % (zellen, 100 * ST.familienfehler(zellen)))
    print("     ueber benachbarte Horizonte, nicht nach einer Einzelzelle "
          "(2.208-n86).")
    print()

    reihen = B.lade()
    mom = momentum250(reihen)
    # ⚠️⚠️ DIE LAGE HAENGT AN DER ZIELGROESSE, nicht umgekehrt
    # (`messnorm.ZIELGROESSE_JE_LAGE`): `bewegung_r` gehoert zu
    # `spot x einstieg`, `barriere` zu `hebel x einstieg`. Der erste
    # Lauf hatte fuer beide `spot` gesetzt und alle neun
    # barriere-Zellen mit einer Fehlermeldung quittiert - richtig
    # abgelehnt von der Norm, falsch gestellt von mir. Abgeleitet
    # statt aufgezaehlt, damit eine Aenderung der Tabelle hier
    # ankommt.
    lagen = {}
    for (inst, strat), zg in N.ZIELGROESSE_JE_LAGE.items():
        if zg in ziele and zg not in lagen and inst in ("spot", "hebel"):
            lagen[zg] = N.Lage(instrument=inst, strategie=strat,
                               simuliert=(inst == "hebel"))

    arme = [("ALT", alt, gemeinsam),
            ("NEU", neu, gemeinsam),
            ("NEU-VOLL", neu, None)]
    ergebnis: dict = {}

    for ziel in ziele:
        if ziel not in N.ZIELGROESSEN:
            print("  unbekannte Zielgroesse %r - erlaubt: %s"
                  % (ziel, ", ".join(sorted(N.ZIELGROESSEN))))
            return 2
        print("-" * 112)
        print("  ZIELGROESSE: %s%s" % (
            ziel, "   ⚠️ HAUPTZELLE - die registrierte Tabelle steht darauf"
            if ziel == "bewegung_r" else
            "   (Quote-Kanal, Zielhoehe %.1f R - daran haengt der HEBEL)"
            % ZIELHOEHE))
        print("-" * 112)
        print("  %-9s %3s %6s %6s %9s %20s %9s %7s  %s"
              % ("Arm", "H", "Syms", "Menge", "Wirkung", "Band", "Bezug",
                 "Bloecke", "Urteil"))
        for H in horizonte:
            _SPEICHER.clear()
            for name, quelle, filter_ in arme:
                try:
                    je0 = K.baue(reihen, "turnover", quelle, horizont=H)
                except Exception as exc:                   # noqa: BLE001
                    print("  %-9s %3d -> %s" % (name, H, str(exc)[:60]))
                    continue
                if ziel == "barriere":
                    je0, _a = auf_barriere(je0, _barrieren(reihen, H), ab)
                # ⚠️ NEU-VOLL bekommt KEINEN Symbolfilter, aber dasselbe
                # Fenster und dieselbe Mindestbesetzung - sonst waere der
                # Unterschied teils ein Fenster- und kein Mengeneffekt.
                je = beschneiden(je0, filter_ or None, ab)
                if not je:
                    print("  %-9s %3d -> leere Welt (kein Ankertag mit 12 "
                          "Besetzungen)" % (name, H))
                    continue
                syms = len({x["sym"] for z in je.values() for x in z})
                # ⚠⚠ ZWEI MENGEN, ZWEI FRAGEN. `menge_nach_datenlage`
                # waehlt je Arm die beste (F-212) - richtig fuer die Frage
                # "traegt es?". Fuer den ARMVERGLEICH ist es falsch: im
                # Probelauf bekam NEU-VOLL 5 % und NEU 50 %, und dann
                # mischt die Differenz Symbolmenge UND Auswahlanteil.
                # Genau die Falle "die Grundgesamtheit ist keine
                # Stellschraube", hier im eigenen Vergleich.
                menge = (fest_menge or
                         MA.menge_nach_datenlage(je, mom, horizont=H))
                if menge is None:
                    print("  %-9s %3d %6d %6s -> KEINE Menge haelt Anker UND "
                          "Bloecke" % (name, H, syms, "-"))
                    continue
                try:
                    b = MA.pruefe_auswahl(
                        "turnover", je, mom, lage=lagen[ziel],
                        menge=menge,
                        rng=np.random.default_rng(saat), horizont=H,
                        hypothese="C Kalibrierung Free Float",
                        verwendung="Beitrag", zielgroesse=ziel)
                except Exception as exc:                   # noqa: BLE001
                    print("  %-9s %3d -> %s" % (name, H, str(exc)[:66]))
                    continue
                ergebnis.setdefault((ziel, name), {})[H] = b
                print("  %-9s %3d %6d %6s %+9.4f [%+.4f..%+.4f] %+9.4f %7d  %s"
                      % (name, H, syms, menge, b.wirkung, b.unten, b.oben,
                         b.bezugswert, b.n_bloecke, kurz(b.urteil)),
                      flush=True)
            print()

    # ---- DIE AUSWERTUNG ------------------------------------------------
    print("=" * 112)
    print("  WAS DIE DREI ARME ZUSAMMEN SAGEN")
    print("=" * 112)
    for ziel in ziele:
        print("  %s:" % ziel)
        for name, _q, _f in arme:
            je_h = ergebnis.get((ziel, name), {})
            if not je_h:
                print("    %-9s keine auswertbare Zelle" % name)
                continue
            traegt = sorted(h for h, b in je_h.items() if b.traegt)
            zeile = " ".join("H%d:%+.4f%s" % (h, je_h[h].wirkung,
                                              "*" if je_h[h].traegt else "")
                             for h in sorted(je_h))
            print("    %-9s %s   traegt bei %s"
                  % (name, zeile,
                     ("H" + ", H".join(str(h) for h in traegt)) if traegt
                     else "KEINEM Horizont"))
        a = ergebnis.get((ziel, "ALT"), {})
        n = ergebnis.get((ziel, "NEU"), {})
        v = ergebnis.get((ziel, "NEU-VOLL"), {})
        beide = sorted(set(a) & set(n))
        if beide:
            d = [n[h].wirkung - a[h].wirkung for h in beide]
            print("    ➤ GROESSE (NEU minus ALT, gleiche Symbole): "
                  "%s · Median %+.4f R"
                  % (" ".join("H%d:%+.4f" % (h, n[h].wirkung - a[h].wirkung)
                              for h in beide), float(np.median(d))))
        beide2 = sorted(set(n) & set(v))
        if beide2:
            d2 = [v[h].wirkung - n[h].wirkung for h in beide2]
            print("    ➤ MENGE (NEU-VOLL minus NEU, gleiche Groesse): "
                  "%s · Median %+.4f R"
                  % (" ".join("H%d:%+.4f" % (h, v[h].wirkung - n[h].wirkung)
                              for h in beide2), float(np.median(d2))))
        print()
    print("  ⚠️ EIN VORZEICHEN IST KEIN BEFUND. Getragen hat, was das Band "
          "vom Nullpunkt")
    print("     trennt - und eine FORM ueber benachbarte Horizonte, keine "
          "Einzelzelle.")
    print("  Dauer %.1f min" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
