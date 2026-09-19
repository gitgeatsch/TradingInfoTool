# -*- coding: utf-8 -*-
"""V2: DIE BASISLINIE DER VERKAUFSSEITE (19.09.2026, Paket V, Plan § 12).

Die Verkaufsseite hat bis heute keine einzige Zahl darueber, ob ein Verkauf
richtig war (2.392). Seit dem Morgenlauf vom 19.09. liegen die ersten
Ergebnisse vor: 273 Ausstiege mit vollem H20, 543 mit H5
(2.468-k19-k20). Dieses Skript macht daraus die BASISLINIE.

⚠️⚠️ WAS HIER GEMESSEN WIRD - UND WAS NICHT. Heute entscheidet allein das
Sprachmodell, was verkauft wird; der Ausstieg verzweigt vor allen
Bewertungsstufen. Gemessen wird deshalb zwangslaeufig DAS MODELL, nicht eine
Bewertung. Das ist der Arm ,heutige Rolle` des gepaarten Versuchs und der
Stand, gegen den V3 spaeter antreten muss - mehr ist es nicht.

⚠️⚠️ UND ES IST NUR EINE VON VIER VERKAUFSFRAGEN (Nutzergespraech 19.09.):

    1 es gibt Besseres        relative Entwicklung  ->  NICHT gefragt
    2 die Position ist zu gross  Portfoliorisiko    ->  NICHT gefragt
    3 Gewinnmitnahme          Folgebewegung nach Anstieg  -> hier, getrennt
    4 Absicherung             Folgebewegung nach Schwaeche -> hier, getrennt

Fall 1 ist der einzige, der auf einer bereits gemessenen Grundlage steht
(Auswahl: beste zwei, +2,74 % H20, t 4,52) - er gehoert nach V3, nicht
hierher.

## Die sechs Entscheidungen (Nutzer, 19.09.)

    E1  ECHTER Kurs aus `price_cache` statt Tagesschluss; Tagesschluss als
        Gegenprobe. ⚠️ Der Grund: bei einer Empfehlung um 14:00 und
        Messung gegen den Schluss um 23:59 liegen zehn Stunden Bewegung VOR
        dem Ausstieg bereits in der Zahl. Alle 273 haben einen
        15-Minuten-Kurs im Umkreis von 15 Minuten (2.463).
    E2  Zielgroesse in R (`stop_ziel_atr` 2,5 x ATR14). ⚠️ DIE EINHEIT IST
        GELIEHEN: der Spot-Bestand hat keinen Stop. Sie wird nur benutzt,
        damit die Zahl mit der Kette (+0,0403 R) vergleichbar ist.
    E3  H5 mit NORMURTEIL (37 Tage, `band()` braucht 30), H20 als HINWEIS
        (22 Tage, `band()` braucht 120 - das ist Arithmetik, keine Wahl).
    E4  Nullwelt: zufaellige Zeitpunkte desselben Symbols im selben
        Fenster, 40 Ziehungen.
    E5  getrennt nach REDUZIEREN und VERKAUFEN - in den Rohzahlen laufen
        sie gegenlaeufig.
    E6  getrennt nach der LAGE DAVOR: verkauft nach Anstieg
        (Gewinnmitnahme) oder nach Schwaeche (Absicherung).

⚠️ Vorzeichen: POSITIV heisst, der Verkauf war richtig (der Kurs ist
danach gefallen). Beide Richtungen zaehlen - sonst misst man die Haelfte,
die man sehen will.

⚠️ Nur lesend gegen die Tagessicherung. Kein LLM.
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import os
import shutil
import sqlite3
import sys
import tempfile
import time

import numpy as np

import messnorm
import phase3_takt as T
from n64_schnitt_stufen import band

HORIZONTE = (5, 20)
NORMFAEHIG = 5            # nur H5 traegt ein Band (E3)
VORLAUF_TAGE = 20         # fuer die Lage DAVOR (E6)
NULL_ZIEHUNGEN = messnorm.NULL_ZIEHUNGEN
SAAT = 20260919
VORBEHALT = ("BASISLINIE: gemessen wird, ob DAS MODELL richtig lag - nicht ob "
             "eine Bewertung traegt. Eine von vier Verkaufsfragen (3 und 4). "
             "Die R-Einheit ist geliehen: Spot hat keinen Stop")


def neueste_sicherung() -> sqlite3.Connection:
    """Die neueste Tagessicherung, EINMAL ausgepackt und wiederverwendet.

    ⚠️⚠️ WARUM NICHT `mkdtemp()` JE LAUF (gelernt am 19.09.2026): jede
    Sicherung ist rund 140 MB entpackt. Ein neues Verzeichnis je Aufruf hat
    im Lauf eines Tages 19 GB im Temp-Ordner abgelegt und die Systemplatte
    auf 3 GB freien Speicher gebracht - der naechste Lauf brach mit
    ,No space left on device` ab. Der Zielpfad traegt jetzt den Namen der
    Quelle: dieselbe Sicherung wird wiederverwendet, eine neue ersetzt sie
    nicht, sondern kommt daneben (alte Kopien loescht man bewusst).

    ⚠️ Die Produktion bleibt unberuehrt: gelesen wird eine KOPIE, und die
    nur `mode=ro`."""
    p = sorted(glob.glob("K:/My Drive/Claude_Austauschordner/DB_Backups/*.db.gz"))[-1]
    ordner = os.path.join(tempfile.gettempdir(), "tit_sicherungen")
    os.makedirs(ordner, exist_ok=True)
    z = os.path.join(ordner, os.path.basename(p)[:-3])
    if not os.path.exists(z) or os.path.getsize(z) < 1_000_000:
        with gzip.open(p, "rb") as ein, open(z, "wb") as aus:
            shutil.copyfileobj(ein, aus)
        print("  Sicherung ausgepackt: %s" % os.path.basename(p))
    else:
        print("  Sicherung (wiederverwendet): %s" % os.path.basename(p))
    return sqlite3.connect("file:%s?mode=ro" % z.replace("\\", "/"), uri=True)


def lade_ausstiege(con) -> list:
    """Die Ausstiege der Rollen-Kette - ALLE, nicht nur die fertig verfolgten.

    ⚠️⚠️ HIER STAND `ausstieg_outcome_status = 'gemessen'`, UND DAS WAR
    FALSCH (korrigiert 19.09.2026, beim ersten Lauf aufgefallen). ,gemessen`
    heisst: BEIDE Horizonte sind fertig. Fuer H5 wirft dieser Filter jede
    Zeile weg, deren H20 noch laeuft - 543 gueltige H5-Werte ueber 37 Tage
    schrumpften so auf 273 ueber 22, und damit fiel H5 unter die
    Bandgrenze. Die Voranalyse hatte die richtige Zahl genannt, die Messung
    die falsche Menge genommen.
    #
    ⚠️ WAS STATTDESSEN ENTSCHEIDET: die Kursverfuegbarkeit, und zwar JE
    HORIZONT. Fehlt der Punkt bei t+h, faellt der Fall fuer DIESEN Horizont
    weg - nicht fuer den anderen.

    ⚠️ NUR DIE ROLLEN-KETTE. Neun Zeilen ohne `quelle_kette` stammen aus der
    alten Logik; sie hier mitzuzaehlen hiesse, zwei Entscheider in eine Zahl
    zu legen."""
    aus = []
    for sym, ts, aktion, b5, b20 in con.execute(
            "SELECT symbol, created_at, action, ausstieg_bewegung_5_pct,"
            " ausstieg_bewegung_20_pct FROM signals"
            " WHERE quelle_kette = 'rollen'"
            " AND action IN ('VERKAUFEN', 'REDUZIEREN')"):
        t = T._zeit(ts)
        if t is not None:
            aus.append({"symbol": sym, "zeit": t, "aktion": aktion,
                        "tagesschluss": {5: b5, 20: b20}})
    return aus


def lage_davor(kurse: dict, a: dict) -> float | None:
    """Die Entwicklung der letzten %d Tage VOR dem Ausstieg (E6).

    ⚠️ AUS DEMSELBEN 15-MINUTEN-RASTER wie alles andere hier - eine zweite
    Kursquelle waere die naechste Stelle zum Auseinanderlaufen.""" % VORLAUF_TAGE
    reihe = kurse.get(a["symbol"])
    if not reihe:
        return None
    p0 = T.kurs_bei(reihe[0], reihe[1], a["zeit"])
    pv = T.kurs_bei(reihe[0], reihe[1],
                    a["zeit"] - dt.timedelta(days=VORLAUF_TAGE))
    if not p0 or not pv:
        return None
    return (p0 - pv) / pv


def bewegung_nach(kurse: dict, atr: dict, anker: list, horizont: int,
                  versatz: dict | None = None) -> dict:
    """tag -> Liste der Bewegungen in R. POSITIV = der Verkauf war richtig.

    `versatz` verschiebt den Ausstiegszeitpunkt je Anker - das ist die
    Nullwelt (E4): derselbe Bestand, aber ein zufaelliger Moment."""
    aus = collections.defaultdict(list)
    for i, a in enumerate(anker):
        reihe = kurse.get(a["symbol"])
        r_einheit = atr.get(a["symbol"])
        if not reihe or not r_einheit:
            continue
        t0 = a["zeit"] + dt.timedelta(days=float((versatz or {}).get(i, 0.0)))
        p0 = T.kurs_bei(reihe[0], reihe[1], t0)
        p1 = T.kurs_bei(reihe[0], reihe[1], t0 + dt.timedelta(days=horizont))
        if not p0 or not p1:
            continue
        # ⚠️ (p0 - p1): faellt der Kurs, ist der Wert POSITIV - der Verkauf
        # war richtig. Das ist dieselbe Richtungsregel wie in
        # `ausstieg_verfolgung.bewegung`.
        aus[t0.date().isoformat()].append(
            (p0 - p1) / p0 / (T.STOP_ATR * r_einheit))
    return dict(aus)


def je_tag(werte: dict) -> dict:
    """Die Tagesklammer: ein Wert je Tag, sonst zaehlen dichte Tage doppelt."""
    return {t: float(np.median(v)) for t, v in werte.items() if v}


def urteile(name: str, echt: dict, nullwerte: list, horizont: int) -> None:
    """Ausgabe mit Band, wo es eines gibt - und ohne, wo keines bildbar ist."""
    tage = len(echt)
    block = messnorm._block(horizont)
    genug = tage >= 2 * block
    punkt = float(np.mean(list(echt.values()))) if echt else float("nan")
    nw = float(np.mean(nullwerte)) if nullwerte else float("nan")
    if genug:
        b = band(echt, block)
        spanne = ("[%+.4f .. %+.4f]" % (b[1], b[2])) if b else "kein Band"
    else:
        # ⚠️ NICHT NACHTRAEGLICH UMDEUTEN: `band()` braucht 2 x Blocklaenge.
        # Bei H20 sind das 120 Tage; vorhanden sind 22. Wer hier trotzdem
        # eine Spanne ausgibt, erfindet sie.
        spanne = "KEIN BAND (%d Tage, %d noetig)" % (tage, 2 * block)
    print("     %-34s %+9.4f %-28s %+9.4f %+9.4f %5d"
          % (name, punkt, spanne, nw, punkt - nw, tage))


def main() -> int:
    t0 = time.time()
    print("=" * 108)
    print("V2 - DIE BASISLINIE DER VERKAUFSSEITE")
    print("=" * 108)
    print("  ⚠️ %s" % VORBEHALT)
    con = neueste_sicherung()
    anker = lade_ausstiege(con)
    print("  %d verfolgte Ausstiege" % len(anker))
    kurse = T.lade_kurse(con)
    atr = T.lade_atr()
    print("  %d Symbole mit 15-Minuten-Kursen · %d mit ATR" % (len(kurse), len(atr)))

    # ---- E1: was die echte Kursquelle gegenueber dem Tagesschluss aendert
    print("\n  E1 · DIE GEGENPROBE - echter Kurs gegen Tagesschluss")
    for h in HORIZONTE:
        echt = bewegung_nach(kurse, atr, anker, h)
        n_echt = sum(len(v) for v in echt.values())
        alt = [a["tagesschluss"][h] for a in anker
               if a["tagesschluss"].get(h) is not None]
        print("     H%-3d echter Kurs: %4d Werte · Tagesschluss: %4d Werte"
              % (h, n_echt, len(alt)))
    print("     ⚠️ Die beiden Reihen sind NICHT ineinander umrechenbar: der")
    print("        Tagesschluss steht in Prozent, der echte Kurs in R.")

    rng = np.random.default_rng(SAAT)
    lagen = {i: lage_davor(kurse, a) for i, a in enumerate(anker)}

    gruppen = [("alle Ausstiege", lambda i, a: True),
               ("nur VERKAUFEN", lambda i, a: a["aktion"] == "VERKAUFEN"),
               ("nur REDUZIEREN", lambda i, a: a["aktion"] == "REDUZIEREN"),
               ("nach ANSTIEG (Gewinnmitnahme)",
                lambda i, a: (lagen.get(i) or 0.0) > 0),
               ("nach SCHWAECHE (Absicherung)",
                lambda i, a: (lagen.get(i) or 0.0) < 0)]

    for h in HORIZONTE:
        art = "NORMURTEIL" if h == NORMFAEHIG else "HINWEIS (kein Band bildbar)"
        print("\n  H%d · %s" % (h, art))
        print("     %-34s %9s %-28s %9s %9s %5s"
              % ("Menge", "R", "Band", "Nullwelt", "entzerrt", "Tage"))
        for name, filt in gruppen:
            teil = [a for i, a in enumerate(anker) if filt(i, a)]
            if len(teil) < 20:
                print("     %-34s zu wenige Faelle (%d)" % (name, len(teil)))
                continue
            echt = je_tag(bewegung_nach(kurse, atr, teil, h))
            if len(echt) < 5:
                print("     %-34s zu wenige Tage (%d)" % (name, len(echt)))
                continue
            nullwerte = []
            for z in range(NULL_ZIEHUNGEN):
                versatz = {i: float(rng.integers(-25, 26))
                           for i in range(len(teil))}
                n = je_tag(bewegung_nach(kurse, atr, teil, h, versatz))
                if n:
                    nullwerte.append(float(np.mean(list(n.values()))))
            urteile(name, echt, nullwerte, h)

    # ---- DIE POSITIVKONTROLLE --------------------------------------------
    #
    # ⚠️ OHNE SIE IST AUCH EIN BAND KEIN URTEIL. Gepflanzt wird ein
    # bekannter Betrag auf die Tageswerte: faellt der Kurs nach dem
    # Ausstieg um `d` R staerker, war der Verkauf um genau `d` R
    # richtiger. Findet die Anlage das nicht wieder, misst sie nichts -
    # dann verschluckt die Tagesklammer oder das Band den Effekt.
    print("\n  POSITIVKONTROLLE (alle Ausstiege, H%d)" % NORMFAEHIG)
    grund = je_tag(bewegung_nach(kurse, atr, anker, NORMFAEHIG))
    basis = float(np.mean(list(grund.values()))) if grund else float("nan")
    for d in (0.02, 0.05, 0.10, 0.20):
        m = float(np.mean([v + d for v in grund.values()]))
        print("     +%.2f R gepflanzt -> gemessen %+.4f (Basis %+.4f, Differenz %+.4f)"
              % (d, m, basis, m - basis))

    print("\n  LESEART")
    print("     R          positiv = der Kurs ist nach dem Ausstieg GEFALLEN,")
    print("                der Verkauf war also richtig. In Stopweiten (2,5 x ATR14).")
    print("     Nullwelt   derselbe Bestand, aber ein zufaelliger Zeitpunkt")
    print("                (%d Ziehungen, Versatz bis 25 Tage)." % NULL_ZIEHUNGEN)
    print("     entzerrt   was von UNSEREN Zeitpunkten uebrig bleibt.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 108)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
