# -*- coding: utf-8 -*-
"""Tragen Volumen und Groesse als EIGENSTAENDIGER Beitrag? (29.08.2026)

**Nutzerauftrag:** *"ja pruefe Volumen und Groesse als eigenstaendigen
Beitrag"*.

## Was hier ANDERS gefragt wird als am 23.08.

Am 23.08. wurde gemessen, ob eine Eigenschaft den Vorsprung einer REGEL
verstaerkt (`messe_tagewahl_je_eigenschaft.py`) - Ergebnis flach. Das ist eine
Frage nach dem VERSTAERKER.

Hier wird nach dem BEITRAG gefragt:

    Bewegt sich ein Asset mit hohem Volumen staerker als eines mit
    niedrigem - am selben Tag, unter denselben Marktbedingungen?

## Die Konstruktion

  EIGENSCHAFT   Mittel der letzten 252 Handelstage VOR dem Stichtag.
                Nie der Stichtag selbst - sonst flieszt Tagesrauschen ein,
                und eine Eigenschaft ist ein Zustand, kein Ereignis.
  RANGPLATZ     quer ueber ALLE Assets desselben Kalendertags. Damit ist
                die Marktlage konstant gehalten - der Vergleich ist
                zwischen Assets, nicht zwischen Tagen.
  ZIELGROESZE   die Bewegung ueber H Tage, in ZWEI Fassungen:
                  roh      in Prozent
                  in R     geteilt durch die eigene Schwankungsbreite
                ⚠️ Die zweite ist die entscheidende: wir handeln in R.
                Was sich nach Normierung wegkuerzt, ist kein Beitrag.

## ⚠️ DIE EHRLICHE EINHEIT IST DER KALENDERTAG (Methodik 2.84)

Krypto laeuft synchron. Tausende Datenpunkte an 2.000 Tagen sind keine
tausenden unabhaengigen Ziehungen. Deshalb:

    je Kalendertag EIN Zusammenhang -> die Streuung UEBER DIE TAGE ist
    das Fehlermasz, nicht die Zahl der Datenpunkte.

## Vorab festgelegt, VOR dem Lauf

  traegt      Zusammenhang in R ungleich null, ueber die Tage stabil,
              und der Vorzeichentest ueber die Tage haelt
  traegt nicht  Zusammenhang in R nicht von null zu trennen
  ⚠️ nur roh   ein Effekt, der nach der R-Normierung verschwindet, ist
              die Volatilitaet in anderer Schreibweise - KEIN Beitrag
"""
import sqlite3
import statistics as st
import sys

import numpy as np

# ⚠️ NUR BEIM EIGENEN CLI-AUFRUF (04.09.2026, gefunden beim ersten Import
# dieser Datei aus pruefe_pakete.py, F-204). `_Mitschnitt` dort ersetzt
# stdout durch einen Tee-Wrapper ohne `reconfigure()` - ein ungeschuetzter
# Aufruf liesse jeden Import dieser BASIS-Funktion (44 abhaengige Skripte)
# an einem fremden Betriebszweck scheitern.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

DB = "file:data/messdaten.db?mode=ro"
RUECKBLICK = 252          # Handelstage fuer die Eigenschaft
SCHWANKUNG = 14           # Handelstage fuer die Schwankungsbreite
MIND_ASSETS = 15          # weniger als das ist kein Querschnitt


def lade():
    """Kursreihen je Symbol: Datum, Schluss, Volumen - NUR KRYPTO.

    ⚠️⚠️ GEFUNDEN 04.09.2026 (N-17b, Gegenprobe der Zufallskontrolle).
    Bis N-19 (03.09.) enthielt `data/messdaten.db` ausschliesslich Krypto -
    diese Funktion filterte deshalb nie explizit und war trotzdem richtig.
    Seit N-19 traegt dieselbe Tabelle zusaetzlich Aktien/ETF/Rohstoffe
    (469+293+35 von 1313 Symbolen). Ohne Filter mischte jede nachgelagerte
    Messung (44 Skripte importieren diese Funktion) beide Welten - eine
    US-Aktie und ein Coin landen im selben Tagesquerschnitt.

    GEFUNDEN, NICHT VERMUTET: die Zufallskontrolle in
    `messe_form_kurz_gegen_lang.py` schlug bei einem vollen Lauf an
    (+0,0002 R, Band schliesst Null knapp aus) - das Werkzeug erklaerte
    sich damit selbst fuer ungueltig, genau wie vorgesehen. Ursache
    zurueckverfolgt: 798 von 1314 Symbolen waren Nicht-Krypto.

    ⚠️ Frueher gelaufene Messungen, die zusaetzlich `funding` oder
    `turnover` (Umlaufmenge) VERLANGEN, waren dabei kaum betroffen - beide
    Datenquellen sind faktisch krypto-exklusiv (nur `DASH`, dieselbe alte
    Namenskollision aus F-198/F-201, hatte einen Treffer). Das war aber
    Zufall der Datenlage, kein Schutz durch Design - ab jetzt filtert
    diese Funktion selbst."""
    c = sqlite3.connect(DB, uri=True)
    roh = {}
    for sym, tag, schluss, hoch, tief, vol in c.execute(
            "SELECT symbol, date, close, high, low, volume "
            "FROM price_history_ohlc WHERE currency='USD' "
            "AND assetklasse='krypto' "
            "AND close IS NOT NULL AND close > 0 ORDER BY symbol, date"):
        roh.setdefault(sym, []).append(
            (tag[:10], float(schluss), float(hoch or schluss),
             float(tief or schluss), float(vol or 0.0)))
    c.close()
    return {s: v for s, v in roh.items() if len(v) > RUECKBLICK + 60}


def spanne(hoch, tief, schluss, n):
    """Mittlere Tagesspanne der letzten n Tage - unsere Schwankungsbreite."""
    s = np.maximum(hoch - tief, np.abs(np.diff(np.concatenate(([schluss[0]],
                                                               schluss)))))
    aus = np.full(len(schluss), np.nan)
    for i in range(n, len(schluss)):
        aus[i] = s[i - n:i].mean()
    return aus


def baue(reihen, horizont):
    """Je Kalendertag: Rangplaetze der Eigenschaften + Bewegung."""
    je_tag = {}
    for sym, zeilen in reihen.items():
        tage = [z[0] for z in zeilen]
        schluss = np.array([z[1] for z in zeilen])
        hoch = np.array([z[2] for z in zeilen])
        tief = np.array([z[3] for z in zeilen])
        vol = np.array([z[4] for z in zeilen])
        umsatz = vol * schluss                      # Groessennaeherung
        breite = spanne(hoch, tief, schluss, SCHWANKUNG)
        for i in range(RUECKBLICK, len(schluss) - horizont):
            if not np.isfinite(breite[i]) or breite[i] <= 0:
                continue
            v = vol[i - RUECKBLICK:i]
            u = umsatz[i - RUECKBLICK:i]
            if v.mean() <= 0 or u.mean() <= 0:
                continue
            weg = schluss[i + horizont] - schluss[i]
            je_tag.setdefault(tage[i], []).append({
                "volumen": float(v.mean()),
                "umsatz": float(u.mean()),
                "roh": float(weg / schluss[i]),
                "in_r": float(weg / breite[i])})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_ASSETS}


def rang(werte):
    o = np.argsort(np.argsort(np.asarray(werte, float)))
    return o / max(len(o) - 1, 1)


def zusammenhang(je_tag, eigenschaft, ziel, mische=False, rng=None):
    """Je Kalendertag ein Zusammenhang. Rueckgabe: Liste ueber die Tage."""
    aus = []
    for tag in sorted(je_tag):
        z = je_tag[tag]
        e = rang([x[eigenschaft] for x in z])
        y = rang([x[ziel] for x in z])
        if mische:
            e = rng.permutation(e)
        if np.std(e) > 0 and np.std(y) > 0:
            aus.append(float(np.corrcoef(e, y)[0, 1]))
    return aus


def urteil(name, werte):
    if not werte:
        print("  %-34s keine Tage" % name)
        return
    m = st.mean(werte)
    sd = st.stdev(werte) if len(werte) > 1 else 0.0
    t = m / (sd / len(werte) ** 0.5) if sd else 0.0
    pos = sum(1 for x in werte if x > 0)
    print("  %-34s %+.4f   t = %+6.2f   %4d von %4d Tagen positiv (%.0f %%)"
          % (name, m, t, pos, len(werte), 100 * pos / len(werte)))


def main():
    reihen = lade()
    print("=" * 78)
    print("TRAGEN VOLUMEN UND GROESSE ALS EIGENSTAENDIGER BEITRAG?")
    print("=" * 78)
    print("Reihen: %d   Rueckblick fuer die Eigenschaft: %d Handelstage"
          % (len(reihen), RUECKBLICK))
    rng = np.random.default_rng(20260829)
    for horizont in (5, 20):
        je_tag = baue(reihen, horizont)
        if not je_tag:
            continue
        n = st.median([len(z) for z in je_tag.values()])
        print()
        print("-" * 78)
        print("HORIZONT %d Handelstage  --  %d Kalendertage, im Mittel %d Assets je Tag"
              % (horizont, len(je_tag), n))
        print("-" * 78)
        for eigenschaft, klar in (("volumen", "VOLUMEN (Stueck)"),
                                  ("umsatz", "GROESSE (Umsatz USD)")):
            print()
            print("  %s" % klar)
            urteil("roh, in Prozent", zusammenhang(je_tag, eigenschaft, "roh"))
            urteil("⚠️ in R (entscheidend)", zusammenhang(je_tag, eigenschaft, "in_r"))
            urteil("Negativkontrolle (gemischt)",
                   zusammenhang(je_tag, eigenschaft, "in_r", True, rng))
        print()
        print("  POSITIVKONTROLLE")
        urteil("Bewegung gegen sich selbst", zusammenhang(je_tag, "roh", "roh"))


if __name__ == "__main__":
    main()
