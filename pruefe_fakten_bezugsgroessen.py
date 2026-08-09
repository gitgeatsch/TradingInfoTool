"""Welcher Zahlenparameter erreicht das LLM OHNE Bezugsgroesse? (2026-08-09)

DIE FRAGE (Nutzer, 09.08.): *"die Parameter die an das LLM uebergeben werden
sollen einen neutralen Ausgangswert erhalten, damit wird der Parameter erst
brauchbar."* Genau so ist es - und der Fall, an dem es aufgefallen ist, war
nur einer von vielen.

DAS PRINZIP. Eine nackte Zahl ist fuer das Modell nicht lesbar. "Trefferquote
16 %" liest sich katastrophal und liegt in Wahrheit 10,7 Prozentpunkte unter
einer Latte von 26,7 %. "ATR 3,2" ist ohne Perzentil weder hoch noch niedrig.
"Funding 0,00003" ist ohne Vergleich gar nichts. Gemessen am 09.08. hat genau
diese Nacktheit die LONG-Konfidenz um bis zu 33 Punkte gedrueckt.

WAS ALS BEZUG GILT - eines davon reicht, und alle sind im Projekt schon in
Gebrauch:

    einstufung / label / trend    kategorial vorklassifiziert (fear_greed,
                                  dollar_index, btc_trend_label)
    perzentil / rang              Position in der eigenen Verteilung
                                  (atr_perzentil)
    breakeven / basislinie        die Latte, gegen die der Wert gehoert
                                  (Trefferquote, Systemguete)
    baender / vorsprung           Abstand zur mechanischen Basislinie
                                  (crv_baender)
    schwelle / minimum / maximum  der Wert, ab dem es kippt
    median / mittel / spanne      Bezug innerhalb derselben Groesse
    hinweis / lesehilfe           Klartext-Einordnung im selben Block

WAS DIESE DATEI NICHT TUT: entscheiden, ob ein Fakt einen Bezug BRAUCHT.
Manche Zahlen sind selbsterklaerend (ein Kurs, eine Anzahl, ein Datum). Die
Datei liefert die Liste; die Entscheidung je Fakt gehoert in die
Fakten-Entscheidungsmappe.

    python pruefe_fakten_bezugsgroessen.py --db <kopie.db>
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys

# Wortstaemme, die einen Bezug anzeigen. Bewusst grosszuegig - lieber ein
# Fakt zu wenig gemeldet als eine Liste, die niemand durchsieht.
BEZUG = ("einstufung", "label", "trend", "perzentil", "rang", "breakeven",
         "basislinie", "baender", "vorsprung", "schwelle", "minimum",
         "maximum", "median", "mittel", "spanne", "hinweis", "lesehilfe",
         "einordnung", "geschrumpft", "quelle", "gesamttendenz", "zustand",
         "kategorie", "profil", "richtung", "typ", "wert", "note")

# Zahlen, die aus sich heraus verstaendlich sind und keinen Bezug brauchen.
SELBSTERKLAEREND = re.compile(
    r"(preis|usd|eur|kurs|anzahl|count|datum|date|zeit|stunde|tage?|"
    r"_von$|_bis$|entry|stop_loss|take_profit|liquidation|menge|"
    r"hebel|leverage|pct_von|pct_bis)", re.I)


def _zahlenblaetter(obj, pfad="", aus=None):
    """Alle Zahlen-Endknoten mit ihrem Pfad und den Geschwisterschluesseln."""
    aus = aus if aus is not None else []
    if isinstance(obj, dict):
        geschwister = set(obj)
        for k, v in obj.items():
            neu = f"{pfad}.{k}" if pfad else k
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                # Den WERT gleich mitgeben. Ihn spaeter ueber den Pfad
                # nachzuschlagen scheitert an zwei Stellen: Listenpfade ("[]")
                # sind nicht rueckverfolgbar, und Schluessel MIT PUNKT
                # (fibonacci "0.0") zerfallen beim Aufteilen. Beides ergab
                # `None` - und ein None-Wert landete dann faelschlich in
                # "ohne Bezug", weil die Groessenordnung nicht pruefbar war.
                aus.append((neu, k, geschwister, v))
            else:
                _zahlenblaetter(v, neu, aus)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):   # Listen stichprobenartig
            _zahlenblaetter(v, f"{pfad}[]", aus)
    return aus


def hat_bezug(schluessel: str, geschwister: set) -> bool:
    """Traegt der Schluessel selbst oder ein Geschwister einen Bezug?"""
    text = " ".join([schluessel] + sorted(geschwister)).lower()
    return any(b in text for b in BEZUG)


def _anker(fakten: dict) -> dict:
    """Die BLOCKUEBERGREIFENDEN Bezugsgroessen des Faktensatzes.

    WARUM DAS NOETIG IST. Die erste Fassung suchte Bezuege nur im selben
    Block und meldete deshalb `technische_analyse.ema.20 = 0,0088` als
    "ohne Bezug" - dabei steht der Kurs im Block `preis` und das Modell
    kann direkt vergleichen. Von 43 gemeldeten Parametern waren so rund
    zwanzig Fehlalarme. Ein Pruefwerkzeug, dessen Liste zur Haelfte aus
    Rauschen besteht, wird nicht durchgesehen."""
    preis = (fakten.get("preis") or {}).get("usd")
    atr = (fakten.get("technische_analyse") or {}).get("atr")
    atr_rel = atr.get("relativ_prozent") if isinstance(atr, dict) else None
    return {"preis": preis if isinstance(preis, (int, float)) else None,
            "atr_relativ_prozent": atr_rel if isinstance(atr_rel, (int, float))
            else None}


def bezug_ueber_bloecke(pfad: str, wert: float, anker: dict) -> str | None:
    """Ist der Wert gegen eine Groesse AUSSERHALB seines Blocks lesbar?

    Heuristik, und sie sagt es selbst: die Groessenordnung entscheidet. Ein
    Wert in der Naehe des Kurses ist eine Kursgroesse und gegen `preis.usd`
    lesbar. Ein Prozentwert ist gegen `atr.relativ_prozent` lesbar, WENN das
    Modell den Vergleich auch ziehen soll - deshalb wird er nur dort
    angenommen, wo der Schluessel selbst nach Prozent aussieht.
    """
    preis = anker.get("preis")
    if preis and preis > 0 and wert != 0:
        verhaeltnis = abs(wert) / preis
        # Kursskala: gleiche Groessenordnung wie der Kurs (Faktor 20 in
        # beide Richtungen deckt Bollinger, EMA, Fibonacci, Zonenpreise).
        if 0.05 <= verhaeltnis <= 20:
            return "Kursskala - lesbar gegen preis.usd"
    if anker.get("atr_relativ_prozent") and re.search(r"prozent|pct|_pp$", pfad, re.I):
        return "Prozentskala - lesbar gegen technische_analyse.atr.relativ_prozent"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--tabelle", default="hebel_signals")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    r = conn.execute(
        f"SELECT facts_json f, symbol, created_at FROM {args.tabelle} "
        f"WHERE facts_json IS NOT NULL ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if not r:
        print("Kein Faktensatz gefunden.")
        return 1
    fakten = json.loads(r["f"])
    print(f"Echter Faktensatz: {r['symbol']} vom {str(r['created_at'])[:16]}")
    print(f"{len(fakten)} Bloecke\n")

    anker = _anker(fakten)
    print(f"Blockuebergreifende Anker: preis.usd={anker['preis']}, "
          f"atr.relativ_prozent={anker['atr_relativ_prozent']}")
    print()

    blaetter = _zahlenblaetter(fakten)
    ohne, mit, ueber, egal = [], [], [], []
    for pfad, schluessel, geschwister, w in blaetter:
        if SELBSTERKLAEREND.search(schluessel) or SELBSTERKLAEREND.search(pfad):
            egal.append(pfad)
            continue
        if hat_bezug(schluessel, geschwister):
            mit.append(pfad)
            continue
        quelle = bezug_ueber_bloecke(pfad, w, anker)
        (ueber if quelle else ohne).append((pfad, w, quelle))

    print(f"Zahlen-Parameter gesamt: {len(blaetter)}")
    print(f"  selbsterklaerend (Kurs, Anzahl, Datum ...): {len(egal)}")
    print(f"  Bezug im selben Block:                      {len(mit)}")
    print(f"  Bezug ueber Bloecke hinweg:                 {len(ueber)}")
    print(f"  OHNE jeden Bezug:                           {len(ohne)}")
    print()
    if ueber:
        print("BEZUG UEBER BLOECKE - lesbar, aber nur indirekt:")
        for pfad, w, quelle in sorted(ueber):
            print(f"   {pfad:50} = {str(w)[:14]:14} {quelle}")
        print()
    if ohne:
        print("OHNE JEDEN BEZUG - fuer das Modell nicht einordenbar:")
        for pfad, w, _ in sorted(ohne):
            print(f"   {pfad:50} = {w}")
    print()
    print("LESEART: das ist eine LISTE, kein Urteil. Manche dieser Zahlen")
    print("brauchen keinen Bezug. Die Entscheidung je Fakt gehoert in die")
    print("Fakten-Entscheidungsmappe - diese Datei sorgt nur dafuer, dass sie")
    print("bewusst getroffen wird statt vergessen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
