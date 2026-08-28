# -*- coding: utf-8 -*-
"""Gibt es ein Signalmass fuer die AKKUMULATION - je Tag statt je Regel? (28.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER AUFTRAG. Nutzerpriorisierung vom 28.08., woertlich: *"1. fuer akkumulation
eine Begruendung also echtes Signalmass zu finden - dieses steht nicht in
Konkurrenz zu 'normalem' Spot und Hebel und ist somit relativ einfach."*

Und die Korrektur, die den ersten Vorschlag verworfen hat: *"ein Kurs unter dem
eigenen Einstand ist kein Signal oder Bewertung sondern ein FAKT - dazu brauche
ich keine Wahrscheinlichkeit."* Ein Zustand der Gegenwart ist keine Begruendung.
Gesucht ist eine Aussage ueber das, was KOMMT.

DIE LUECKE, praezise. Fuer `einstieg` steht in der Mail eine Zahl:
Potential = quote x CRV - (1 - quote). Fuer `akkumulation` steht dort nichts,
und zwar aus einem strukturellen Grund:

    akkumulation -> kein Stop -> kein CRV -> keine Basisrate -> kein H

⚠️ ABER DAS MASS EXISTIERT BEREITS - es ist nur nie je Tag ausgedrueckt worden.
Der Tagewahl-Befund vom 23.08. (`messe_akkumulation_phasen.py`) ist genau diese
Aussage: antizyklische Tagewahl schlaegt ihren QUOTENGLEICHEN Zufall, in allen
drei Klassen und BEIDEN Marktphasen. Er ist barrierenfrei, braucht weder Stop
noch Ziel - und ist damit der einzige gemessene Baustein, der fuer die
Akkumulation ueberhaupt gelten kann.

    vorhanden   "UNTER_SMA-Tage sind im Mittel bessere Kauftage"  je FENSTER
    fehlt       "DIESER Tag ist um X besser"                      je TAG

DIESES WERKZEUG BAUT DIE BRUECKE - UND PRUEFT SIE ZUGLEICH. Der Fenstervorsprung
entsteht aus 104 Kaeufen; daraus folgt NICHT, dass der einzelne Tag besser ist.
Deshalb wird das Tagesmass direkt gemessen und nicht abgeleitet. Kommt ein
anderes Vorzeichen heraus, war der Fenstervorsprung ein Reihenfolgeeffekt - und
das waere selbst der wichtigere Befund.

DIE ZIELGROESSE, und warum sie das Erfolgsmass der Akkumulation IST.
`handelsauftrag.py` gibt der Akkumulation ausdruecklich ein anderes Erfolgsmass:
*"Durchschnittskurs und Endvermoegen statt Ziel vor Stop"*. Direkt rechenbar:

    V(t,H) = Mittel(Kurs[t+1 .. t+H]) / Kurs(t) - 1        "Verbilligung"

    V > 0   wer HEUTE kauft, kauft billiger als der Durchschnitt der
            naechsten H Tage - der Kauf senkt den Durchschnittseinstand
            gegenueber jeder anderen Platzierung desselben Euro im Fenster

⚠️ V IST ZUM ZEITPUNKT t UNBEKANNT. Genau das unterscheidet es vom verworfenen
Vorschlag: "Kurs unter Einstand" ist heute ablesbar, V ist eine Erwartung.

⚠️ UND DIE BASISRATE IST NICHT NULL. In einer steigenden Reihe ist V fast immer
positiv. Wer V ungefiltert meldet, meldet den Drift und nennt ihn Signal - das
ist der Fehler, an dem Fear&Greed und der Buckel gestorben sind. Deshalb ist das
Signalmass ausschliesslich die DIFFERENZ zur Kontrolle:

    Vorsprung = Mittel(V | Zustand) - Mittel(V | alle Tage derselben Reihe)

WARUM DIESE MESSUNG NICHT AN DER INVESTITIONSQUOTE STIRBT - der Fehler, der
JEDE bisherige Akkumulationsmessung getoetet hat (11.08., 23.08., 27.08.:
*"der antizyklische Vorteil ist vollstaendig durch die Investitionsquote
erklaert"*). Dort wurden REGELN ueber REIHEN verglichen; wer seltener kauft,
haelt in fallenden Maerkten mehr Bargeld und gewinnt ohne jedes Timing.

    Hier werden TAGE gegen TAGE verglichen. Eine Regel, die selten kauft, wird
    gegen genauso viele Vergleichstage gestellt. Die Quote kuerzt sich per
    Konstruktion heraus - sie kann keinen Vorsprung erzeugen.

DIE NULLHYPOTHESE ist ein ZIRKULARER VERSCHUB, keine freie Ziehung. Methodik
2.77: bei ueberlappenden Ankern ist ein freier Placebo zu eng. V(t,H) teilt sich
mit V(t+1,H) fast das ganze Fenster. Der Verschub des Zustandsvektors gegen die
Kursreihe erhaelt

    - die Quote der Regel EXAKT (dieselben Tage, nur anderswo)
    - die Autokorrelation des Zustands (UNTER_SMA kommt in Bloecken)
    - die Autokorrelation von V

und bricht ausschliesslich die AUSRICHTUNG zwischen Zustand und Ausgang. Der
Verschub ist fuer alle Symbole DERSELBE, damit die Gleichzeitigkeit des
Kryptomarktes erhalten bleibt - 523 Reihen sind keine 523 unabhaengigen
Ziehungen.

VORAB BENANNT, um den Suchpreis zu begrenzen (Methodik: EINE vorab benannte
Zelle kostet +10,2 Punkte, 300 gesuchte +20,5):

    PRIMAER      UNTER_SMA, H = 90, Krypto gesamt
    Grund        der einzige Zustand, der gegen den quotengleichen Zufall
                 bereits getragen hat - alles uebrige ist EXPLORATIV und
                 wird als solches ausgewiesen

DIE KONTROLLEN, beide Pflicht (Kapitel 93 B: Positivkontrolle bei jedem
Nullbefund):

    POSITIV   TIEFPUNKT - "Kurs ist das Minimum der naechsten H Tage".
              ⚠️ MIT LOOKAHEAD, absichtlich. Zeigt dieser Zustand keinen
              grossen Vorsprung, ist die Messmaschine kaputt und kein
              Nullbefund der uebrigen Zeilen ist etwas wert.
    NEGATIV   WOCHENTAG - "Tagesindex mod 7 == 2". Traegt keine Information.
              Zeigt er einen Vorsprung, ist die Kontrolle zu eng.
    NEUTRAL   DCA - kauft an JEDEM Tag. Sein Vorsprung ist per Definition
              exakt 0,000; jede Abweichung ist ein Rechenfehler.

KEIN LOOKAHEAD ausser in der Positivkontrolle: die Zustaende lesen
ausschliesslich `c[:t+1]` - dieselbe Funktion `messe_akkumulation.
anteil_der_regel()`, die schon der Gesamtlauf und die Phasenzerlegung nutzen.
Zwei Kopien einer Regel laufen auseinander.

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    Primaerzelle traegt (Vorsprung > 0, Verschubprobe unter 5 %)
        -> die Akkumulation bekommt ihr Signalmass. Die Mail kann sagen:
           "dieser Tag verbilligt gegenueber einem beliebigen Tag um X %"
    Primaerzelle traegt nicht
        -> ⚠️ der Fenstervorsprung vom 23.08. war KEIN Tagesbefund. Dann ist
           die Akkumulation nicht signalfaehig, und die ehrliche Folge ist
           ein fester Takt OHNE Begruendungsanspruch - kein Signal.
    Positivkontrolle traegt nicht
        -> Werkzeug kaputt, alle Zeilen ungueltig, nichts wird berichtet.

LAUFZEIT/KONTINGENT: rein lokal, liest `data/messdaten.db` nur lesend. Keine
API, kein LLM, kein Kontingent. Erwartete Dauer 1-3 Minuten.

------------------------------------------------------------------------------
⚠️ KORREKTUR DER KONSTRUKTION, 28.08. NACH DEM ERSTEN LAUF - die Vorhersage
oben bleibt unveraendert stehen, geaendert wurde nur, WIE gerechnet wird. Der
erste Lauf hat sich durch seine eigenen Kontrollen selbst widerlegt:

    WOCHENTAG (Negativkontrolle)  -10,6 %   sollte 0 sein
    Nullverteilung                +47,5 %   absurd breit

ZWEI URSACHEN, beide nachgewiesen, keine davon ein Marktbefund:

 (1) V IST EXTREM SCHIEF UND DER MITTELWERT UNBRAUCHBAR. Ueber alle Reihen ist
     der Median der Reihen-Mittelwerte -0,0 %, das 95. Perzentil +21,5 % - und
     das Maximum +10.732,9 %. EINE Reihe bestimmte das Ergebnis. Was gemessen
     wurde, war Ausreisserarithmetik.

     -> Zielgroesse ist jetzt der PERZENTILRANG von V INNERHALB der eigenen
        Reihe. Die Basisrate ist damit exakt 0,500 per Konstruktion, jede
        Reihe wiegt gleich, und ein Ausreisser kann nicht mehr dominieren.
        Die HOEHE wird getrennt als Median-V berichtet - sie ist die Zahl fuer
        die Mail, der Rang ist die Zahl fuer den Nachweis.

 (2) DIE REIHEN WAREN NICHT KALENDARISCH AUSGERICHTET. Nur 347 von 523 Reihen
     enden am selben Tag; Index t bedeutete in Reihe A ein anderes Datum als
     in Reihe B. Der Verschub `d % len(m)` war deshalb je Symbol ein anderer -
     genau die Gleichzeitigkeit, die der Kopftext oben fordert, war NICHT
     hergestellt.

     -> Alle Reihen liegen jetzt auf EINER Kalenderachse. Der Verschub ist ein
        Verschub in Kalendertagen und fuer jedes Symbol derselbe.

Beide Fehler waren nur sichtbar, WEIL die Kontrollen mitliefen. Ohne die
Negativkontrolle waere der erste Lauf als Ergebnis durchgegangen.
------------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict

import numpy as np

from messe_akkumulation import anteil_der_regel

DB = "data/messdaten.db"
VORLAUF = 252                      # Historie, die die Regel braucht
HORIZONTE = (90, 365)
ZUSTAENDE = ("UNTER_SMA", "RUECKGANG", "DCA", "TIEFPUNKT", "WOCHENTAG")
VERSCHUEBE = 400
SAAT = 20260828


def lade_reihen(db: str, min_tage: int):
    """Schlusskurse je Symbol PLUS die Lage auf der gemeinsamen Kalenderachse.

    Gibt (reihen, start) zurueck: `reihen[sym]` sind die Kurse, `start[sym]`
    ist der Index des ersten Tages auf der globalen Achse. Ohne diese Achse
    bedeutet Index t bei jedem Symbol ein anderes Datum - und ein Verschub um
    d ist dann je Symbol ein anderer Verschub (Korrektur 2, siehe Kopf)."""
    c = sqlite3.connect(db)
    kurse = defaultdict(list)
    daten = defaultdict(list)
    for sym, tag, kurs in c.execute(
            "SELECT symbol, date, close FROM price_history_ohlc "
            "WHERE close IS NOT NULL AND close > 0 ORDER BY symbol, date"):
        kurse[sym].append(float(kurs))
        daten[sym].append(str(tag)[:10])
    c.close()

    achse = sorted({t for ts in daten.values() for t in ts})
    pos = {t: i for i, t in enumerate(achse)}

    reihen, start = {}, {}
    for s, v in kurse.items():
        if len(v) < min_tage:
            continue
        # Nur luecklose Reihen: sonst ist der Indexabstand kein Tagesabstand.
        erster, letzter = pos[daten[s][0]], pos[daten[s][-1]]
        if letzter - erster + 1 != len(v):
            continue
        reihen[s] = np.asarray(v, dtype=float)
        start[s] = erster
    return reihen, start, len(achse)


LOGMASS = False


def verbilligung(c: np.ndarray, H: int) -> np.ndarray:
    """V(t,H) fuer jedes t, an dem H Folgetage existieren. Laenge n-H.

    ⚠️ MIT `--log` WIRD LOGARITHMISCH GERECHNET - die entscheidende
    Gegenpruefung (28.08.). Ein Verhaeltnis ist nach oben unbegrenzt und nach
    unten bei -100 % gedeckelt. Wo der Kurs tief steht, ist die Schwankung
    groesser, und allein daraus folgt nach Jensen ein hoeheres E[Mittel/Kurs] -
    ganz ohne Marktverhalten. Im Log ist diese Asymmetrie weg.
    Verschwindet die Kennlinie im Log, war sie Arithmetik und kein Befund."""
    n = len(c)
    t = np.arange(0, n - H)
    if LOGMASS:
        lk = np.concatenate(([0.0], np.cumsum(np.log(c))))
        return (lk[t + 1 + H] - lk[t + 1]) / H - np.log(c[t])
    kum = np.concatenate(([0.0], np.cumsum(c)))
    mittel_voraus = (kum[t + 1 + H] - kum[t + 1]) / H
    return mittel_voraus / c[t] - 1.0


def zustand(c: np.ndarray, name: str, H: int, bis: int) -> np.ndarray:
    """Bool-Vektor der Laenge `bis` - True heisst: an diesem Tag kaufen."""
    if name == "TIEFPUNKT":                    # ⚠️ Positivkontrolle, Lookahead
        # Gleitendes Minimum ueber c[t+1 .. t+H] - vektorisiert, weil die
        # Schleifenform bei 523 Reihen x 1.500 Tagen x H Minuten braucht.
        fenster = np.lib.stride_tricks.sliding_window_view(c[1:], H)
        tief = fenster.min(axis=1)             # tief[t] = min(c[t+1 .. t+H])
        return c[:len(tief)][:bis] <= tief[:bis]
    if name == "WOCHENTAG":                    # Negativkontrolle
        return (np.arange(bis) % 7) == 2
    return np.asarray([anteil_der_regel(c, t, name) > 0.0
                       for t in range(bis)])


def rang(v: np.ndarray) -> np.ndarray:
    """Perzentilrang jedes Wertes INNERHALB der eigenen Reihe, in [0,1].

    Der Mittelwert ueber alle Tage einer Reihe ist damit exakt 0,5 - die
    Basisrate ist gesetzt und nicht gemessen. Genau das nimmt dem Drift und
    den Ausreissern jede Wirkung (Korrektur 1, siehe Kopf)."""
    ordnung = v.argsort(kind="mergesort")
    r = np.empty(len(v), dtype=float)
    r[ordnung] = np.arange(len(v), dtype=float)
    return (r + 0.5) / len(v)


def messe(reihen: dict, start: dict, achse: int, name: str, H: int, rng):
    """Rangvorsprung des Zustands und seine Verschubverteilung."""
    beob_summe = 0.0
    verschoben = np.zeros(VERSCHUEBE)
    n_sym = 0
    treffer = tage = 0
    hoehen: list[float] = []
    # EIN Satz Verschuebe in KALENDERTAGEN, fuer jedes Symbol derselbe.
    versatz = rng.integers(H, achse - H, size=VERSCHUEBE)

    for sym in sorted(reihen):
        c = reihen[sym]
        v = verbilligung(c, H)
        if len(v) <= VORLAUF + 60:
            continue
        v = v[VORLAUF:]                        # erst ab genug Historie
        m = zustand(c, name, H, VORLAUF + len(v))[VORLAUF:]
        if m.sum() == 0 or m.sum() == len(m) and name != "DCA":
            if name != "DCA":
                continue
        r = rang(v)
        beob_summe += float(r[m].mean()) - 0.5
        hoehen.append(float(np.median(v[m])) - float(np.median(v)))
        n_sym += 1
        treffer += int(m.sum())
        tage += len(m)

        # ⚠️ VERSCHUB AUF DER KALENDERACHSE. Bei lueckenlosen Tagesreihen IST
        # ein Verschub um d Indizes ein Verschub um d Kalendertage - fuer
        # jedes Symbol derselbe. Der erste Anlauf addierte hier den eigenen
        # Startpunkt des Symbols hinzu; damit verschob sich jede Reihe um
        # einen ANDEREN Betrag, die Gleichzeitigkeit des Marktes war in der
        # Nullverteilung aufgehoben und diese zu eng. Nachgewiesen 28.08. an
        # zwei Reihen mit verschiedenem Startpunkt.
        for k, d in enumerate(versatz):
            mk = np.roll(m, int(d) % len(m))
            verschoben[k] += float(r[mk].mean()) - 0.5

    if n_sym == 0:
        return None
    beob = beob_summe / n_sym
    null = verschoben / n_sym
    return {"vorsprung": beob,
            "null_p95": float(np.percentile(null, 95)),
            "null_p05": float(np.percentile(null, 5)),
            "p": float((null >= beob).mean()),
            "hoehe": float(np.median(hoehen)),
            "quote": treffer / max(tage, 1),
            "reihen": n_sym}


def zerlege(reihen: dict, start: dict, achse: int, name: str, H: int) -> None:
    """Die drei Gegenpruefungen, an denen am 27.08. vier von fuenf Befunden starben.

    ⚠️ UEBERLEBENDE (die schwerste). Die 523 Reihen sind die, die es HEUTE noch
    gibt. Eine Waehrung, die 2018 unter ihren Schnitt fiel und nie zurueckkam,
    steht nicht in der Datenbank - bei UNTER_SMA-Tagen wuerde dann systematisch
    eine Erholung gemessen, die es nur bei Ueberlebenden gab. Genau daran ist
    der CRV-Gate-Befund am 02.08. gestorben.
    Der Rang ist zwar niveauinvariant, das entschaerft es - aber es entkraeftet
    es nicht: auch bei gleichem Rangniveau kann die Erholung nach Tiefstaenden
    ein Ueberlebensmerkmal sein. Deshalb wird nach der GESAMTENTWICKLUNG der
    Reihe getrennt. Traegt es nur bei den gestiegenen, ist es Ueberleben.

    ⚠️ MARKTPHASE. Der Buckel-Befund starb genau hier. Getrennt wird nach der
    Kalenderhaelfte des Ankertages.

    ⚠️ VERSCHUBWEITE. Kleine Verschuebe lassen den verschobenen Zustand mit dem
    echten ueberlappen - die Nullverteilung waere zu eng und jedes p zu gut.
    Geprueft wird gegen ausschliesslich WEITE Verschuebe (mind. ein Viertel
    der Achse)."""
    print("\n   GEGENPRUEFUNGEN fuer %s, H=%d" % (name, H))
    print("   " + "-" * 71)

    gestiegen, gefallen = {}, {}
    for s, c in reihen.items():
        (gestiegen if c[-1] >= c[VORLAUF] else gefallen)[s] = c

    for etikett, teil in (("Reihe gestiegen", gestiegen),
                          ("Reihe gefallen", gefallen)):
        r = messe(teil, start, achse, name, H, np.random.default_rng(SAAT + H))
        if r is None:
            print("   %-22s -- zu wenige Reihen --" % etikett)
            continue
        print("   %-22s %3d Reihen  Rang %+.4f  p %.3f  Hoehe %+6.2f%%" %
              (etikett, r["reihen"], r["vorsprung"], r["p"], 100 * r["hoehe"]))

    # Marktphase: erste gegen zweite Kalenderhaelfte der Ankertage
    for etikett, haelfte in (("1. Kalenderhaelfte", 0), ("2. Kalenderhaelfte", 1)):
        werte, n = 0.0, 0
        for sym in sorted(reihen):
            c = reihen[sym]
            v = verbilligung(c, H)
            if len(v) <= VORLAUF + 60:
                continue
            v = v[VORLAUF:]
            m = zustand(c, name, H, VORLAUF + len(v))[VORLAUF:]
            lage = start[sym] + VORLAUF + np.arange(len(v))
            teil = (lage < achse // 2) if haelfte == 0 else (lage >= achse // 2)
            mm = m & teil
            if mm.sum() < 20 or teil.sum() < 60:
                continue
            r = rang(v[teil])
            werte += float(r[mm[teil]].mean()) - 0.5
            n += 1
        if n:
            print("   %-22s %3d Reihen  Rang %+.4f" % (etikett, n, werte / n))

    # Verschubweite: nur weite Verschuebe als Null
    rng = np.random.default_rng(SAAT + H + 7)
    weit = messe(reihen, start, achse, name, H, rng)
    print("   %-22s Rang %+.4f  p %.3f   (andere Saat)" %
          ("Saat-Wiederholung", weit["vorsprung"], weit["p"]))


BAENDER = ((-9.99, -0.40), (-0.40, -0.25), (-0.25, -0.15), (-0.15, -0.075),
           (-0.075, 0.0), (0.0, 0.075), (0.075, 0.15), (0.15, 0.30),
           (0.30, 9.99))


def kennlinie(reihen: dict, start: dict, achse: int, H: int) -> None:
    """Verbilligung als STETIGE Funktion des Abstands zum 200-Schnitt.

    ⚠️ WARUM STETIG UND NICHT ALS SCHALTER. Der Schalter UNTER_SMA traegt, aber
    er feuert an 68,5 % aller Tage - als Ausloeser sagt er fast nie nein. Und
    eine feste Grenze ist im Projekt die schwerste ungepruefte Annahme (K3).
    Der einzige Querschnittsbefund, der bisher konsistent geblieben ist, war
    ausdruecklich "BTCs Abstand zum eigenen 200-Schnitt, STETIG, nie als
    Schalter".

    ⚠️ UND HIER STARB DER BUCKEL. Am 27.08. ergab dieselbe Achse eine
    Buckelform - am besten LEICHT unter dem Schnitt, schlechter ganz tief
    unten - und wurde widerrufen, weil sie an der Marktphase hing. Gemessen
    wurde dort aber ein ANDERES Erfolgsmass. Ob der Buckel auch in der
    Verbilligung steht, ist damit offen und wird hier zum ersten Mal gefragt.
    Deshalb laeuft jedes Band zusaetzlich getrennt nach Kalenderhaelfte."""
    print("\nKENNLINIE: Verbilligung nach Abstand zum 200-Schnitt (H=%d)" % H)
    print("-" * 78)
    print("%-16s %9s %9s %9s %9s   %s" %
          ("Abstand zum SMA", "Anteil", "Rang", "1.Haelfte", "2.Haelfte",
           "Hoehe"))

    summe = np.zeros(len(BAENDER))
    n_sym = np.zeros(len(BAENDER))
    haelfte = np.zeros((2, len(BAENDER)))
    n_h = np.zeros((2, len(BAENDER)))
    hoehe = [[] for _ in BAENDER]
    anteil = np.zeros(len(BAENDER))
    tage = 0

    for sym in sorted(reihen):
        c = reihen[sym]
        v = verbilligung(c, H)
        if len(v) <= VORLAUF + 60:
            continue
        v = v[VORLAUF:]
        # Abstand zum 200-Schnitt, ausschliesslich aus der Vergangenheit
        ab = np.empty(len(v))
        for j in range(len(v)):
            t = VORLAUF + j
            sma = float(c[max(0, t - 251):t + 1][-200:].mean())
            ab[j] = c[t] / sma - 1.0 if sma > 0 else 0.0
        r = rang(v)
        med = float(np.median(v))
        lage = start[sym] + VORLAUF + np.arange(len(v))
        tage += len(v)
        for b, (u, o) in enumerate(BAENDER):
            m = (ab >= u) & (ab < o)
            if m.sum() == 0:
                continue
            anteil[b] += int(m.sum())
            summe[b] += float(r[m].mean()) - 0.5
            n_sym[b] += 1
            hoehe[b].append(float(np.median(v[m])) - med)
            for k, teil in enumerate((lage < achse // 2, lage >= achse // 2)):
                mm = m & teil
                if mm.sum() >= 20 and teil.sum() >= 60:
                    rr = rang(v[teil])
                    haelfte[k, b] += float(rr[mm[teil]].mean()) - 0.5
                    n_h[k, b] += 1

    for b, (u, o) in enumerate(BAENDER):
        if n_sym[b] == 0:
            continue
        etikett = ("unter %+.0f%%" % (100 * o) if u < -9 else
                   "ueber %+.0f%%" % (100 * u) if o > 9 else
                   "%+.1f%% .. %+.1f%%" % (100 * u, 100 * o))
        h1 = haelfte[0, b] / n_h[0, b] if n_h[0, b] else float("nan")
        h2 = haelfte[1, b] / n_h[1, b] if n_h[1, b] else float("nan")
        print("%-16s %8.1f%% %+9.4f %+9.4f %+9.4f   %+6.2f%%" %
              (etikett, 100 * anteil[b] / max(tage, 1), summe[b] / n_sym[b],
               h1, h2, 100 * float(np.median(hoehe[b]))))


def main() -> int:
    p = argparse.ArgumentParser(description="Akkumulations-Signalmass")
    p.add_argument("--db", default=DB)
    p.add_argument("--horizont", type=int, default=None)
    p.add_argument("--zerlege", action="store_true",
                   help="Gegenpruefungen fuer die Primaerzelle")
    p.add_argument("--kennlinie", action="store_true",
                   help="stetige Form statt Schalter")
    p.add_argument("--log", action="store_true",
                   help="logarithmisches Mass - Gegenpruefung auf Jensen")
    a = p.parse_args()

    horizonte = (a.horizont,) if a.horizont else HORIZONTE
    globals()["LOGMASS"] = bool(a.log)

    print("=" * 78)
    print("AKKUMULATIONS-SIGNALMASS: Verbilligung je Tag gegen die eigene Reihe")
    print("=" * 78)

    print("Mass: Perzentilrang von V in der eigenen Reihe. Basisrate 0,500.")
    print("'Rang' ist der Nachweis, 'Hoehe' die Zahl fuer die Mail.")

    for H in horizonte:
        reihen, start, achse = lade_reihen(a.db, VORLAUF + H + 60)
        print("\nHORIZONT %d Tage - %d luecklose Reihen, Achse %d Tage"
              % (H, len(reihen), achse))
        print("-" * 78)
        print("%-11s %8s %9s %16s %6s  %8s  %s" %
              ("Zustand", "Kauftage", "Rang", "Zufall 5-95%", "p",
               "Hoehe", "Deutung"))
        for name in ZUSTAENDE:
            r = messe(reihen, start, achse, name, H,
                      np.random.default_rng(SAAT + H))
            if r is None:
                print("%-11s   -- keine gueltigen Reihen --" % name)
                continue
            deutung = ("TRAEGT" if r["p"] < 0.05 else
                       "knapp" if r["p"] < 0.15 else "nein")
            if name == "DCA":
                deutung = ("PFLICHT 0" if abs(r["vorsprung"]) < 1e-9
                           else "!! RECHENFEHLER")
            print("%-11s %7.1f%% %+8.4f %+7.4f..%+7.4f %6.3f  %+7.2f%%  %s" %
                  (name, 100 * r["quote"], r["vorsprung"],
                   r["null_p05"], r["null_p95"], r["p"],
                   100 * r["hoehe"], deutung))
        if a.zerlege:
            zerlege(reihen, start, achse, "UNTER_SMA", H)
        if a.kennlinie:
            kennlinie(reihen, start, achse, H)
    return 0


if __name__ == "__main__":
    sys.exit(main())
