# -*- coding: utf-8 -*-
"""V-0 / N-7: Traegt die heutige Rollen-Kette? (29.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DIE FRAGE, und warum sie Vorrang hat. Das Projekt hat sich die Reihenfolge
selbst gegeben:

    "N-7 hat Vorrang vor N-6: ob ein Eingriff in die Kette sich lohnt, haengt
     davon ab, ob die Kette selbst traegt."

Fuer die ALTE Kette ist die Antwort gemessen und niederschmetternd (09.08.):
LLM-Richtungswahl 29,8 / 27,7 / 25,0 % gegen EMA-200 61,8 / 61,7 / 63,5 % -
"das LLM liegt hinter JEDER Regel". Seit dem Rollenumbau (Prompt 34.611 ->
3.183 Zeichen, zwei Rollen, Z1) existiert KEINE vergleichbare Messung.

DAS MASS IST DIE BEWEGUNG, NICHT DIE ZIELERREICHUNG (Nutzerentscheidung B vom
29.08.). Begruendung, arithmetisch: Ziel = CRV x Stop, Basisrate = 1/(1+CRV) -
die Trefferquote steht fest, BEVOR der Markt etwas tut. Wer "Ziel vor Stop"
misst, misst die eigene Zielregel zurueck.

    B(t,H) = Kurs(t+H) / Kurs(t) - 1        die Bewegung ueber H Tage

    barrierenfrei · brutto · Richtung offen · ohne Gebuehren

⚠️ WARUM 1 UND 2 TAGE, und warum das NICHT zu kurz ist. Die Trennschaerfe
wurde VOR dem Bau gerechnet (Streuung aus 60 Reihen, zweiseitig, 80 % Power):

    Horizont  Signale  Streuung  nachweisbar ab   Urteil
     1 Tag      583      5,3 %       0,61 %       tragfaehig
     2 Tage     480      7,2 %       0,92 %       tragfaehig
     3 Tage     334      8,3 %       1,27 %       zu grob
     5 Tage     130     10,2 %       2,50 %       unbrauchbar

Der staerkste je gemessene Auswahlvorteil des Projekts lag bei +1,01 % (A1).
Auf 3 und 5 Tagen waere er NICHT nachweisbar - dort zu messen hiesse, einen
Nullbefund zu erzeugen, der nichts bedeutet.

Und der kurze Horizont passt zur Sache: die tatsaechliche Haltedauer liegt im
Median bei 0,30 Tagen, das Signal loest nach 2,57 Tagen auf (Kostenmodell
04.08.). ⚠️ Der 1-2-Tage-Horizont ist nicht ein Zugestaendnis an die Datenlage,
sondern der Horizont, auf dem tatsaechlich gehandelt wird.

DIE GRENZE, die bleibt: die Rollen-Kette laeuft erst seit dem 14.08. Fuer die
Trichter-Horizonte 20 und 60 Handelstage gibt es KEINE Signale mit genug
Nachlauf - und das ist keine Datenluecke, sondern das Alter der Kette. Diese
Messung beantwortet die Frage fuer den kurzen Horizont, nicht fuer den langen.

DIE VIER ARME - dieselbe Grundgesamtheit, dieselben Tage:

    KETTE      die Symbol-Tage, an denen die Rollen-Kette KAUFEN sagte
    ZUFALL     gleich viele Symbol-Tage, gewuerfelt (quotengleich)
    REGEL      dieselbe Anzahl, gewaehlt nach "Kurs unter dem 200-Schnitt" -
               die einfache Regel, die die alte Kette geschlagen hat
    ALLE       jeder Symbol-Tag der Grundgesamtheit (die Basislinie)

⚠️ QUOTENGLEICH IST PFLICHT. Wer 583 LLM-Tage gegen 20.000 Zufallstage
vergleicht, misst die Stichprobengroesse mit. Die Kontrolle zieht deshalb
GENAU so viele Tage wie die Kette gewaehlt hat.

GEWERTET WIRD DER PERZENTILRANG von B innerhalb der eigenen Reihe. Basisrate
exakt 0,500 per Konstruktion - damit kann der Drift nicht als Leistung
durchgehen, und keine Ausreisserreihe kann das Ergebnis bestimmen (der Fehler,
an dem die erste Fassung von `messe_akkumulationsmass` starb: eine Reihe mit
+10.732 % bestimmte den gewichteten Mittelwert).

Die HOEHE wird getrennt als Median-Bewegung in Prozent berichtet - sie ist die
Zahl fuer die Deutung, der Rang die Zahl fuer den Nachweis.

DIE KONTROLLEN, beide Pflicht:

    POSITIV   BESTTAG - der Tag mit der hoechsten Folgebewegung je Symbol.
              ⚠️ MIT LOOKAHEAD, absichtlich. Zeigt er keinen Vorsprung, ist
              die Messmaschine kaputt und kein Nullbefund ist etwas wert.
    NEGATIV   WOCHENTAG - jeder siebte Tag. Traegt keine Information.

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    Kette schlaegt Zufall UND Regel (Rang > 0, p < 0,05)
        -> die Kette traegt. V-1 bis V-6 sind sinnvoll, die Bewertungsstufe
           bekommt eine Grundlage.
    Kette schlaegt den Zufall, nicht die Regel
        -> ⚠️ die Kette traegt, ist aber teurer als eine Zeile Code. Dann ist
           die Frage nicht "wie bewerten wir", sondern "warum ein Modell".
    Kette schlaegt den Zufall NICHT
        -> ⚠️⚠️ eine Bewertungsstufe auf dieser Kette filtert Rauschen nach
           Rauschen. V-1 bis V-6 sind auszusetzen, bis die Kette selbst traegt.
    Positivkontrolle traegt nicht
        -> Werkzeug kaputt, nichts wird berichtet.

LAUFZEIT/KONTINGENT: rein lokal. Liest `data/messdaten.db` (Kurse, nur lesend)
und den NB-Export (Signale, nur lesend). Keine API, kein LLM, kein Kontingent.
Erwartete Dauer unter einer Minute.
"""
from __future__ import annotations

import argparse
import json
import io
import sqlite3
import statistics as st
import sys

import numpy as np

NB_EXPORT = (r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten"
             r"/notebook_diagnose.json")
DB = "data/messdaten.db"
EINSTIEG = ("KAUFEN", "NACHKAUFEN", "EROFFNEN")
HORIZONTE = (1, 2)
ZIEHUNGEN = 400
SAAT = 20260829
VORLAUF = 200                      # fuer den 200-Tage-Schnitt der Regel


def lade_reihen(db: str) -> dict:
    """Schlusskurse je Symbol mit Datum, aufsteigend."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    aus: dict = {}
    for sym, tag, kurs in c.execute(
            "SELECT symbol, date, close FROM price_history_ohlc "
            "WHERE close IS NOT NULL AND close > 0 ORDER BY symbol, date"):
        aus.setdefault(sym, ([], []))
        aus[sym][0].append(str(tag)[:10])
        aus[sym][1].append(float(kurs))
    c.close()
    return {s: (t, np.asarray(k, dtype=float)) for s, (t, k) in aus.items()
            if len(k) >= VORLAUF + 30}


def lade_signale(pfad: str) -> list:
    """Kaufempfehlungen der Rollen-Kette: (Symbol, Datum)."""
    d = json.load(io.open(pfad, encoding="utf-8"))
    aus = []
    for s in d.get("spot_signals") or []:
        if s.get("quelle_kette") != "rollen":
            continue
        a = str(s.get("action") or "").replace("\u00d6", "O").upper()
        if a not in EINSTIEG:
            continue
        sym = str(s.get("symbol") or "").upper()
        tag = str(s.get("created_at") or "")[:10]
        if sym and tag:
            aus.append((sym, tag))
    return aus


def bewegung(kurse: np.ndarray, H: int) -> np.ndarray:
    """B(t,H) fuer jedes t, an dem H Folgetage existieren."""
    return kurse[H:] / kurse[:-H] - 1.0


def rang(v: np.ndarray) -> np.ndarray:
    """Perzentilrang in [0,1]. Mittelwert exakt 0,5 per Konstruktion."""
    ordnung = v.argsort(kind="mergesort")
    r = np.empty(len(v), dtype=float)
    r[ordnung] = np.arange(len(v), dtype=float)
    return (r + 0.5) / len(v)


def unter_schnitt(kurse: np.ndarray, bis: int) -> np.ndarray:
    """Die einfache REGEL: Kurs unter dem eigenen 200-Tage-Schnitt.

    Liest nur `kurse[:t+1]` - kein Lookahead. Dieselbe Form wie
    `messe_akkumulation.anteil_der_regel`."""
    aus = np.zeros(bis, dtype=bool)
    for t in range(bis):
        f = kurse[max(0, t - 251):t + 1]
        if len(f) >= VORLAUF:
            aus[t] = kurse[t] < float(f[-VORLAUF:].mean())
    return aus


def messe(reihen: dict, signale: list, H: int, rng) -> dict | None:
    """Die vier Arme plus zwei Kontrollen, je Symbol gerechnet."""
    je_symbol: dict = {}
    for sym, tag in signale:
        if sym in reihen:
            je_symbol.setdefault(sym, set()).add(tag)

    arme = {k: [] for k in ("KETTE", "ZUFALL", "REGEL", "ALLE",
                            "BESTTAG", "WOCHENTAG")}
    hoehen = {k: [] for k in arme}
    treffer = 0

    for sym, tage in sorted(je_symbol.items()):
        daten, kurse = reihen[sym]
        b = bewegung(kurse, H)
        gueltig = len(b)
        if gueltig <= VORLAUF + 20:
            continue
        pos = {d: i for i, d in enumerate(daten[:gueltig])}
        idx = sorted(pos[t] for t in tage if t in pos and pos[t] >= VORLAUF)
        if len(idx) < 3:
            continue

        # Grundgesamtheit: alle Tage mit genug Vorlauf UND Nachlauf
        alle = np.arange(VORLAUF, gueltig)
        r = rang(b[alle])
        lage = {t: i for i, t in enumerate(alle)}
        wahl = np.array([lage[t] for t in idx if t in lage])
        if len(wahl) < 3:
            continue
        treffer += len(wahl)

        arme["KETTE"].append(float(r[wahl].mean()) - 0.5)
        hoehen["KETTE"].append(float(np.median(b[alle][wahl])))
        arme["ALLE"].append(0.0)
        hoehen["ALLE"].append(float(np.median(b[alle])))

        # QUOTENGLEICH: genau so viele Tage wie die Kette gewaehlt hat
        n = len(wahl)
        zuf = [float(r[rng.choice(len(r), n, replace=False)].mean()) - 0.5
               for _ in range(20)]
        arme["ZUFALL"].append(float(np.mean(zuf)))
        hoehen["ZUFALL"].append(float(np.median(b[alle])))

        regel = unter_schnitt(kurse, gueltig)[alle]
        if regel.sum() >= n:
            wo = np.flatnonzero(regel)
            aus = rng.choice(wo, n, replace=False)
            arme["REGEL"].append(float(r[aus].mean()) - 0.5)
            hoehen["REGEL"].append(float(np.median(b[alle][aus])))

        # Positivkontrolle: die n besten Tage (mit Lookahead)
        best = np.argsort(b[alle])[-n:]
        arme["BESTTAG"].append(float(r[best].mean()) - 0.5)
        hoehen["BESTTAG"].append(float(np.median(b[alle][best])))

        # Negativkontrolle: jeder siebte Tag
        wo7 = np.flatnonzero((np.arange(len(alle)) % 7) == 2)
        if len(wo7) >= n:
            aus7 = rng.choice(wo7, n, replace=False)
            arme["WOCHENTAG"].append(float(r[aus7].mean()) - 0.5)
            hoehen["WOCHENTAG"].append(float(np.median(b[alle][aus7])))

    if not arme["KETTE"]:
        return None
    return {"symbole": len(arme["KETTE"]), "signaltage": treffer,
            "arme": {k: (st.mean(v) if v else None) for k, v in arme.items()},
            "hoehen": {k: (st.median(v) if v else None)
                       for k, v in hoehen.items()},
            "roh": arme}


def main() -> int:
    p = argparse.ArgumentParser(description="N-7: traegt die Rollen-Kette?")
    p.add_argument("--db", default=DB)
    p.add_argument("--export", default=NB_EXPORT)
    a = p.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reihen = lade_reihen(a.db)
    signale = lade_signale(a.export)

    print("=" * 76)
    print("V-0 / N-7: TRAEGT DIE HEUTIGE ROLLEN-KETTE?")
    print("=" * 76)
    print("Mass: Bewegung ueber H Tage, barrierenfrei und brutto "
          "(Entscheidung B, 29.08.)")
    print("Gewertet: Perzentilrang in der eigenen Reihe, Basisrate 0,500")
    print("Kaufempfehlungen im Export: %d  ·  Reihen mit Kursen: %d"
          % (len(signale), len(reihen)))

    for H in HORIZONTE:
        r = messe(reihen, signale, H, np.random.default_rng(SAAT + H))
        print()
        print("HORIZONT %d Tag(e) — %s Symbole, %s Signaltage"
              % (H, r["symbole"] if r else "?", r["signaltage"] if r else "?"))
        print("-" * 76)
        if r is None:
            print("  zu wenige Faelle")
            continue
        print("%-11s %10s %12s   %s" % ("Arm", "Rang", "Bewegung", "Lesart"))
        lesart = {
            "KETTE": "was die Rollen-Kette gewaehlt hat",
            "ZUFALL": "quotengleich gewuerfelt — die Kontrolle",
            "REGEL": "Kurs unter dem 200-Schnitt — eine Zeile Code",
            "ALLE": "jeder Tag — die Basislinie",
            "BESTTAG": "MIT Lookahead — Positivkontrolle",
            "WOCHENTAG": "jeder siebte Tag — Negativkontrolle"}
        for k in ("KETTE", "ZUFALL", "REGEL", "ALLE", "BESTTAG", "WOCHENTAG"):
            w, h = r["arme"].get(k), r["hoehen"].get(k)
            if w is None:
                print("%-11s %10s %12s   %s" % (k, "—", "—", lesart[k]))
                continue
            print("%-11s %+10.4f %+11.2f %%   %s"
                  % (k, w, 100 * h, lesart[k]))

        # Der Vergleich, um den es geht
        k, z, g = (r["arme"]["KETTE"], r["arme"]["ZUFALL"],
                   r["arme"].get("REGEL"))
        roh = r["roh"]
        print()
        print("  Kette gegen Zufall: %+.4f" % (k - z), end="")
        if len(roh["KETTE"]) > 2:
            diff = [x - y for x, y in zip(roh["KETTE"], roh["ZUFALL"])]
            sd = st.stdev(diff) if len(diff) > 1 else 0.0
            t = (st.mean(diff) / (sd / len(diff) ** 0.5)) if sd else 0.0
            print("   t = %+.2f  (%d Symbole)" % (t, len(diff)))
        else:
            print()
        if g is not None:
            print("  Kette gegen Regel : %+.4f" % (k - g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
