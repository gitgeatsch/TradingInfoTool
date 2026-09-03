# -*- coding: utf-8 -*-
"""Tragen die Beitraege auch bei der AUSSTIEGSfrage? (03.09.2026)

## Der Anlass — ein Widerspruch im eigenen Code

Die Kette fuehrt zwei Stellen, die dieselbe Groesse verschieden behandeln:

    N-14 (terminmarkt)      nimmt Bestand AUS, weil "bei einem gehaltenen
                            Wert die Ausstiegsfrage ansteht, und die hat
                            die Messung nie beruehrt"
    Stufe 11 (entscheider)  wendet dieselben Beitraege auf genau diese
                            Ausstiegsfragen an

Gemessen (Log 31.08.-03.09.): **230 der 1.491 Signale** sind REDUZIEREN
oder VERKAUFEN. Sie tragen `strategie='einstieg'` - denn die war nie
etwas anderes (F-180) - und werden deshalb mit Beitraegen bewertet, die
auf EINSTIEGEN gemessen wurden.

Dieselbe Begruendung, zwei verschiedene Konsequenzen. Eine davon ist
falsch, und welche, entscheidet diese Messung.

## ⚠️ DIE FORM DER GROESSE — vor der Messung geklaert (Vorgabe)

Die naheliegende Annahme waere: "Ausstieg ist Einstieg mit umgekehrtem
Vorzeichen, also ist es dieselbe Messung." **Das stimmt nicht**, und der
Unterschied liegt nicht in der Kursprognose, sondern in der ANKERMENGE:

    Einstieg   der Zeitpunkt ist FREI waehlbar - jeder Tag, jedes Asset
    Ausstieg   der Wert ist bereits SELEKTIERT - man haelt ihn, weil man
               ihn irgendwann gekauft hat

Eine Groesse kann auf der freien Menge trennen und auf der selektierten
nicht. Genau das ist bei F-170 fuer den Turnover-Rang belegt: er ist zu
52 % eine ASSET-Eigenschaft. Wer nur noch Werte betrachtet, die man
haelt, hat diese Achse teilweise schon festgehalten - und dann bleibt
weniger uebrig, was der Rang noch erklaeren kann.

## ⚠️ Was NICHT geht, und warum

Eine echte Bestandshistorie fuehrt das System nicht - `holdings` kennt
nur den HEUTIGEN Stand. Die Ankermenge "Zeitpunkte, an denen ich diesen
Wert hielt" laesst sich deshalb nicht exakt bilden.

Zwei Naeherungen, beide benannt statt versteckt:

    B  die SYMBOLE, die heute gehalten werden. Staking und Spot-Bestand
       laufen ueber Wochen bis Jahre, die Symbolmenge ist also
       einigermassen stabil. ⚠️ Sie ist trotzdem RUECKBLICKEND gewaehlt.
    C  Zeitpunkte NACH einem Kursanstieg - wer kauft, kauft meist, was
       schon gelaufen ist, und haelt es dann. Das ist die ZEITLICHE
       Selektion, unabhaengig vom Symbol.

B und C sind verschiedene Selektionen. Tragen die Beitraege auf beiden,
ist die Antwort robust; tragen sie nur auf einer, sagt das, welche Achse
die Selektion frisst.

## DIE VORABFESTLEGUNG

    Frage       Trennt der Beitrag die kuenftige Entwicklung auch auf
                einer Ankermenge, die einem BESTAND entspricht?
    Groesse     Funding-Rang und Turnover-Rang, je Kalendertag (2.x
                Tagesklammer), Fuenftel wie im Betrieb
    Regel       dieselbe wie beim Einstieg - das unterste Fuenftel
                sperren; beim Ausstieg heisst "sperren" VERKAUFEN
    Mass        kuenftiger Ertrag ueber H=20 in R, Median je Tag,
                Blockprobe ueber 90+ Tage
    Kontrollen  Negativkontrolle ueber 10 Mischungen (2.104) ·
                Positivkontrolle · GEPAARTER Vergleich A gegen B und
                A gegen C (2.105)

    ⚠️ BEDINGUNG, VOR DEM LAUF GESETZT:
       Der Beitrag traegt bei der Ausstiegsfrage, wenn seine Wirkung auf
       der Bestandsmenge nach Abzug der Negativkontrolle ueber null liegt
       UND der gepaarte Vergleich gegen die freie Menge KEINEN
       nachweisbaren Abfall zeigt.

       Faellt er ab, ist die Potentialschwelle die inkonsistente Stelle.
       Faellt er nicht ab, ist es N-14.

    ⚠️ Und die Ankerzahl wird MITGEDRUCKT. Die Bestandsmenge ist kleiner,
       das Band also breiter - ein "nicht trennbar" darf dann nicht als
       "traegt nicht" gelesen werden (2.x untermaechtig).

    python messe_ausstiegsbeitrag.py [--selbsttest]
"""
import argparse
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_beitragssumme as BS
import messe_funding_niveau as F
import messe_regel_wirksamkeit as W

HORIZONT = BS.HORIZONT
MIND_JE_TAG = BS.MIND_JE_TAG
BLOCK = BS.BLOCK
ANSTIEG_TAGE = 60          # Rueckblick fuer die zeitliche Selektion (C)


def bestandssymbole(db=None):
    """Die Symbole, die HEUTE gehalten werden - inklusive gestaktem.

    ⚠️ UEBER `rollen_eingabe.bestand()`, nicht ueber eine eigene Abfrage.
    `warteschlange._bestand_spot()` fragt `quantity > 0` und uebersieht
    damit sechs vollstaendig gestakte Werte (F-180). Wer hier eine dritte
    Variante baut, bekommt eine dritte Antwort.
    """
    import sqlite3
    from agent import rollen_eingabe as RE
    pfad = db or RE.DB
    aus = set()
    try:
        c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
        for (s,) in c.execute("SELECT symbol FROM holdings"):
            menge, _e = RE.bestand(s, pfad, "spot")
            if menge and float(menge) > 0:
                aus.add(str(s).upper())
    except Exception as exc:                                 # noqa: BLE001
        print("⚠️ Bestand nicht lesbar (%s) - Menge B entfaellt" % exc)
    return aus


def mit_anstieg(reihen, tage_zurueck=ANSTIEG_TAGE):
    """(symbol, tag) -> lief der Wert in den letzten N Tagen POSITIV?

    Die Naeherung fuer "wir sind drin": gekauft wird ueberwiegend, was
    schon gelaufen ist - die Auswahl A1 rankt ausdruecklich nach der
    Entwicklung der letzten 250 Handelstage.
    """
    aus = {}
    for sym, r in reihen.items():
        tage = [z[0] for z in r]
        c = np.array([z[1] for z in r], float)
        for i in range(tage_zurueck, len(c)):
            if c[i - tage_zurueck] > 0:
                aus[(sym.upper(), tage[i])] = bool(
                    c[i] > c[i - tage_zurueck])
    return aus


def teilmenge(je_tag, behalte):
    """Dieselben Anker, gefiltert - und die Tage, die zu duenn werden,
    fallen GANZ weg.

    ⚠️ SONST WAERE DER VERGLEICH KEINER: ein Tag mit drei Werten liefert
    einen Median aus drei Zahlen, und die Fuenftel darauf sind Unsinn.
    Dieselbe Mindestzahl wie in der Grundmessung.
    """
    aus = {}
    for tag, z in je_tag.items():
        teil = [x for x in z if behalte(x, tag)]
        if len(teil) >= MIND_JE_TAG:
            aus[tag] = teil
    return aus


def _wirkung(anker, saaten=10):
    """NETTO, Negativkontrolle ueber mehrere Mischungen, und die Reihe.

    ⚠️ ZEHN MISCHUNGEN, nicht eine (2.104). Am 03.09. haette EINE
    Mischung das Urteil von N-15a gedreht - dieselbe Ankermenge lieferte
    +0,0115 / +0,0069 / +0,0016.
    """
    # ⚠️ `urteil_tage` DRUCKT IMMER. Bei elf Aufrufen je Menge und sechs
    # Mengen waeren das 66 titellose Zeilen, die niemand zuordnen kann -
    # und in denen die drei Zeilen untergehen, auf die es ankommt.
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        netto = M.urteil_tage("", W.wirkung(anker, False)[0],
                              np.random.default_rng(7), BLOCK)
        nullwerte = []
        for s in range(saaten):
            e = M.urteil_tage("", W.wirkung(
                anker, False, mische=np.random.default_rng(900 + s))[0],
                np.random.default_rng(7), BLOCK)
            if e:
                nullwerte.append(e["mittel"])
    return {"netto": netto, "null": float(np.mean(nullwerte)) if nullwerte
            else float("nan"),
            "streuung": float(np.std(nullwerte)) if nullwerte else float("nan"),
            "reihe": W.wirkung(anker, False)[0],
            "anker": sum(len(z) for z in anker.values()),
            "tage": len(anker)}


def _zeile(name, e):
    n = e["netto"]
    if not n:
        print("  %-30s  zu wenig Daten" % name)
        return
    print("  %-30s %+.4f R  [%+.4f .. %+.4f]  %5d Anker · %4d Tage"
          % (name, n["mittel"], n["unten"], n["oben"], e["anker"], e["tage"]))
    print("  %-30s Negativk. %+.4f ± %.4f  ->  bereinigt %+.4f R  %s"
          % ("", e["null"], e["streuung"], n["mittel"] - e["null"],
             "TRAEGT" if n["unten"] > 0 else "nicht trennbar"))


def _gepaart(titel, a, b):
    """Die Differenz JE KALENDERTAG - nicht zwei Baender vergleichen.

    ⚠️ 2.105: bei N-15a ueberlappten die Einzelbaender fast vollstaendig,
    und der Nebeneinander-Vergleich haette in zwei Laeufen zwei
    entgegengesetzte Urteile ergeben. Gepaart kuerzt sich alles Gemeinsame
    heraus - Marktphase, Volatilitaet, die Massverzerrung.
    """
    gem = sorted(set(a) & set(b))
    if len(gem) < 30:
        print("  %s: nur %d gemeinsame Tage - kein Urteil" % (titel, len(gem)))
        return None
    diff = {t: b[t] - a[t] for t in gem}
    e = M.urteil_tage("  %-28s" % titel, diff, np.random.default_rng(7), BLOCK)
    # ⚠️ DIE POSITIVKONTROLLE AUF DIE DIFFERENZ (2.105). Ohne sie ist
    # "nicht trennbar" nicht von "die Anlage sieht es nicht" zu trennen.
    M.urteil_tage("  %-28s" % "  Kontrolle: -0,02 R gesetzt",
                  {t: v - 0.02 for t, v in diff.items()},
                  np.random.default_rng(7), BLOCK)
    return e


def selbsttest():
    """⚠️ Die Kontrolle ist der erste Verdaechtige - erst Kunstdaten.

    Zwei Welten mit bekannter Antwort, und beide muessen richtig
    herauskommen, bevor eine echte Zahl geglaubt wird.
    """
    print("=" * 78)
    print("SELBSTTEST — zwei Welten mit bekannter Antwort")
    print("=" * 78)
    rng = np.random.default_rng(5)
    for name, auf_teilmenge in (
            ("Welt 1: der Beitrag traegt auf BEIDEN Mengen", True),
            ("Welt 2: er traegt NUR auf der freien Menge", False)):
        je_tag = {}
        for d in range(600):
            tag = "2025-%02d-%02d" % (d // 28 + 1, d % 28 + 1)
            z = []
            for k in range(40):
                kennzahl = rng.normal()
                drin = k < 20                     # die "Bestands"-Haelfte
                # ⚠️ -0,84 IST DAS 20-%-QUANTIL der Normalverteilung -
                # also genau das unterste Fuenftel, das die Regel sperrt.
                # Meine erste Fassung schrieb `np.quantile([0.0], 0.0)`,
                # was schlicht 0,0 ist: die Schwelle waere -0,84 statt
                # -0,84 gewesen - zufaellig richtig, aber aus einem
                # sinnlosen Ausdruck. Wer so etwas stehen laesst, hat
                # beim naechsten Parameter keinen Halt mehr.
                schlecht = kennzahl < -0.84
                wirkt = (not drin) or auf_teilmenge
                z.append({"sym": "S%02d" % k, "kennzahl": float(kennzahl),
                          "drin": drin,
                          "in_r": float(rng.normal()
                                        - (0.5 if (schlecht and wirkt) else 0))})
            je_tag[tag] = z
        frei = _wirkung(je_tag, saaten=3)
        teil = _wirkung(teilmenge(je_tag, lambda x, t: x["drin"]), saaten=3)
        traegt_teil = bool(teil["netto"] and teil["netto"]["unten"] > 0)
        print("  %s" % name)
        _zeile("     freie Menge", frei)
        _zeile("     Teilmenge", teil)
        ok = traegt_teil == auf_teilmenge
        print("     erwartet: %s -> %s\n"
              % ("traegt" if auf_teilmenge else "traegt NICHT",
                 "✔" if ok else "✖ DER TEST TAUGT NICHT"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selbsttest", action="store_true")
    p.add_argument("--db", default=None)
    a = p.parse_args()
    if a.selbsttest:
        selbsttest()
        return 0

    # ⚠️ DIESELBEN DREI QUELLEN WIE N-15a, woertlich uebernommen. Meine
    # erste Fassung riet mit `hasattr` an einer Funktion herum, die es
    # nicht gibt - das haette im besten Fall abgestuerzt und im
    # schlechtesten mit leeren Umlaufmengen weitergerechnet, womit der
    # Turnover-Rang still verschwunden waere.
    print("Lade Kurse, Funding und Umlaufmengen ...", flush=True)
    reihen = BS.B.lade()
    funding = F.lade_funding()
    menge = M.reihe("data/onchain_historie.db", "splycur")
    je_tag = BS.baue(reihen, funding, menge)
    print("   %d Kalendertage, %d Anker"
          % (len(je_tag), sum(len(z) for z in je_tag.values())))

    best = bestandssymbole(a.db)
    anstieg = mit_anstieg(reihen)
    print("   Bestandssymbole: %d · davon in der Messbasis: %d"
          % (len(best), len({x["sym"].upper() for z in je_tag.values()
                             for x in z} & best)))

    for feld, name in (("ff_p", "FUNDING-Rang"), ("tf_p", "TURNOVER-Rang")):
        alle = BS._als(je_tag, feld)
        nur_b = BS._als(teilmenge(je_tag, lambda x, t: x["sym"].upper() in best),
                        feld)
        nur_c = BS._als(teilmenge(
            je_tag, lambda x, t: anstieg.get((x["sym"].upper(), t), False)),
            feld)
        print()
        print("=" * 78)
        print("%s — traegt er auch auf einer BESTANDSMENGE?" % name)
        print("=" * 78)
        e_a = _wirkung(alle)
        e_b = _wirkung(nur_b)
        e_c = _wirkung(nur_c)
        _zeile("A  freie Menge (Einstieg)", e_a)
        _zeile("B  nur Bestandssymbole", e_b)
        _zeile("C  nur nach Kursanstieg", e_c)
        print()
        print("  Der GEPAARTE Vergleich — faellt der Beitrag auf der")
        print("  Bestandsmenge ab? (negativ = ja)")
        d_b = _gepaart("B minus A", e_a["reihe"], e_b["reihe"])
        d_c = _gepaart("C minus A", e_a["reihe"], e_c["reihe"])

        print()
        traegt_b = bool(e_b["netto"] and e_b["netto"]["unten"] > 0)
        abfall_b = bool(d_b and d_b["oben"] < 0)
        abfall_c = bool(d_c and d_c["oben"] < 0)
        print("  URTEIL nach der vorab gesetzten Bedingung:")
        print("     traegt auf der Bestandsmenge          %s"
              % ("JA" if traegt_b else "nicht nachweisbar"))
        print("     faellt gegen die freie Menge ab       %s"
              % ("JA (B)" if abfall_b else "nein"))
        print("     faellt nach Kursanstieg ab            %s"
              % ("JA (C)" if abfall_c else "nein"))
        if traegt_b and not (abfall_b or abfall_c):
            print("  -> ✔ DER BEITRAG GILT AUCH BEI DER AUSSTIEGSFRAGE.")
            print("     Dann ist N-14 die inkonsistente Stelle, nicht die")
            print("     Potentialschwelle.")
        elif abfall_b or abfall_c:
            print("  -> ✖ ER FAELLT AB. Dann rechnet die Potentialschwelle")
            print("     bei Bestand mit einer Groesse, die dort nicht")
            print("     nachgewiesen ist.")
        else:
            print("  -> ○ NICHT ENTSCHEIDBAR auf dieser Datenlage.")
            print("     ⚠️ Die Bestandsmenge ist kleiner - das Band ist")
            print("        breiter. Das ist KEIN 'traegt nicht'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
