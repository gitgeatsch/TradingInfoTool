# -*- coding: utf-8 -*-
"""Welche Fakten führen zu welchem Urteil - und tragen sie? (14.08.2026)

DIE FRAGE DES NUTZERS: *"warum erfolgte die Entscheidung, sind die Parameter
die richtigen."*

WARUM NICHT DIE KATEGORIEN DER ALTEN KETTE. Die hatte `top_grund_1..5_kategorie`
mit sieben Werten (technisch, fundamental, risiko, makro, exposure, sektor,
positionierung) - vom Modell vergeben, 2.526 Zeilen. Die Rollen-Kette fuellt
diese Spalten NICHT, und das soll auch so bleiben:

  1. Eine vom Modell vergebene Kategorie ist eine zweite Selbstauskunft ueber
     eine erste. Sagt das Modell "technisch", heisst das nur, dass es sein
     eigenes Argument so nennt.
  2. Sie waere ein zusaetzliches Prompt-Feld - und jede Prompt-Aenderung macht
     die bisherigen Messungen unvergleichbar.

WAS STATTDESSEN GEMESSEN WIRD: aus welchem UNSERER Faktenbloecke der Beleg
stammt. Die Bloecke sind es, die wir bauen und steuern koennen
(`lagebeschreibung.geteilt()`), und die Frage "sind die Parameter die
richtigen" ist genau die Frage, welcher Block etwas beitraegt.

    bestand · struktur · bewegung · marken · volumen · finanzierung · lagebild

DIE ZUORDNUNG IST SCHLUESSELWORT-BASIERT, und das ist eine bewusste Schwaeche.
Sie geht nur deshalb, weil wir die Saetze SELBST erzeugen und ihre Formulierung
kennen. Was nicht zugeordnet werden kann, landet in `unbekannt` und WIRD
AUSGEWIESEN - steigt dieser Anteil, ist die Zuordnung veraltet und nicht etwa
die Datenlage schlecht.

WAS DIESES SKRIPT HEUTE NOCH NICHT KANN: die Ausgaenge dazuhalten. `belege_json`
wird erst seit dem 14.08. geschrieben; die 45 Signale des ersten Echtbetriebs
haben nur den Fliesstext. Bis genug Zeilen MIT Belegen aufgeloest sind, zaehlt
dieses Skript die Verteilung - nicht den Erfolg. Der Unterschied steht im
Bericht.

AUFRUF:  python messe_begruendungen.py [--db PFAD]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict

# Woran ein Beleg seinem Block zugeordnet wird. Die Woerter stammen aus den
# Satzbauern in `agent/lagebeschreibung.py` - wer dort eine Formulierung
# aendert, muss hier nachziehen, und der `unbekannt`-Anteil zeigt es an.
#
# DIE REIHENFOLGE IST TEIL DER DEFINITION, nicht Kosmetik. Sie geht vom
# SPEZIFISCHEN zum GENERISCHEN, weil der erste Treffer gewinnt. In der ersten
# Fassung stand `bewegung` mit "20 tage" weit oben - und schluckte damit den
# Satz "Von den letzten 20 Tagen entfielen 85 % des Umsatzes auf
# Aufwaertstage", der eindeutig zum Volumen gehoert. Ein Wort wie "20 tage"
# kommt in vier Bloecken vor und darf deshalb nicht entscheiden.
BLOCK_WOERTER = {
    # Eindeutige Fachbegriffe zuerst - sie kommen in genau einem Block vor.
    "finanzierung": ("finanzierungsrate", "terminmarkt", "long-positionen",
                     "short-positionen"),
    "marken": ("widerstand", "unterstuetzung", "unterstützung", "beruehrt",
               "berührt"),
    "volumen": ("umsatz", "volumen", "aufwaertstage", "aufwärtstage"),
    "bestand": ("im bestand", "investiert", "einstand"),
    "struktur": ("marktstruktur", "hoehere hochs", "höhere hochs",
                 "tiefere hochs", "tiefere tiefs", "wendepunkt",
                 "bodenbildung", "trendwende", "abwaertstrend",
                 "abwärtstrend", "aufwaertstrend", "aufwärtstrend"),
    "lagebild": ("gesamtmarkt", "assetklassen", "marktbreite", "bitcoin",
                 "rohstoffe", "aktien"),
    # Zuletzt der generischste Block - "Kursentwicklung: 5 Tage ..." ist das,
    # was uebrigbleibt, wenn keiner der obigen Begriffe vorkommt.
    "bewegung": ("kursentwicklung", "handelstage steht", "zum vergleich",
                 "60 handelstage"),
}
VERKAUFSSEITE = ("REDUZIEREN", "VERKAUFEN", "SCHLIESSEN")
KAUFSEITE = ("KAUFEN", "NACHKAUFEN", "ERÖFFNEN")


def block_fuer(text: str) -> str:
    """Aus welchem Faktenblock stammt dieser Beleg?

    ERSTER TREFFER GEWINNT, in der Reihenfolge des Wörterbuchs. Ein Beleg, der
    zwei Bloecke beruehrt ("Widerstand bei steigendem Umsatz"), gehoert
    ohnehin nicht eindeutig zu einem - ihn doppelt zu zaehlen wuerde die Summe
    ueber 100 % treiben und den Vergleich zwischen den Bloecken zerstoeren."""
    t = str(text or "").lower()
    for block, woerter in BLOCK_WOERTER.items():
        if any(w in t for w in woerter):
            return block
    return "unbekannt"


def messe(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row
    spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    hat_belege = "belege_json" in spalten
    felder = "action, unabhaengige_faktoren, outcome_status"
    if hat_belege:
        felder += ", belege_json"
    rows = conn.execute(
        f"SELECT {felder} FROM signals WHERE quelle_kette = 'rollen'"
    ).fetchall()

    # je Block: [Kaufseite, Verkaufsseite, sonst] und je Richtung des Belegs
    verteilung = defaultdict(lambda: defaultdict(int))
    gewichte = defaultdict(lambda: defaultdict(int))
    ausgang = defaultdict(lambda: {"treffer": 0, "aufgeloest": 0})
    mit_belegen = 0
    for r in rows:
        roh = r["belege_json"] if hat_belege else None
        if not roh:
            continue
        try:
            belege = json.loads(roh)
        except (TypeError, ValueError):
            continue
        mit_belegen += 1
        seite = ("kauf" if r["action"] in KAUFSEITE
                 else "verkauf" if r["action"] in VERKAUFSSEITE else "nichts")
        for b in belege:
            block = block_fuer(b.get("fakt"))
            verteilung[block][seite] += 1
            gewichte[block][str(b.get("gewicht") or "?")] += 1
            st = r["outcome_status"]
            if st in ("take_profit_erreicht", "stop_loss_erreicht"):
                ausgang[block]["aufgeloest"] += 1
                if st == "take_profit_erreicht":
                    ausgang[block]["treffer"] += 1
    return {"zeilen": len(rows), "mit_belegen": mit_belegen,
            "hat_spalte": hat_belege, "verteilung": dict(verteilung),
            "gewichte": dict(gewichte), "ausgang": dict(ausgang)}


def bericht(e: dict) -> list[str]:
    z = ["WELCHE FAKTEN FUEHREN ZU WELCHEM URTEIL?", ""]
    if not e["hat_spalte"]:
        z.append("Die Spalte `belege_json` fehlt - aeltere Datenbank.")
        return z
    z.append(f"Signale der Rollen-Kette: {e['zeilen']}, davon mit Belegen: "
             f"{e['mit_belegen']}")
    if not e["mit_belegen"]:
        z += ["",
              "NOCH KEINE BELEGE GESPEICHERT. Die Spalte wird seit dem",
              "14.08.2026 geschrieben; aeltere Zeilen haben nur den",
              "Fliesstext in `short_reasoning`. Das laesst sich NICHT",
              "nachruesten - eine Zeile ohne Belege bleibt ohne Belege.",
              "Nach dem naechsten Lauf hat dieses Skript Datenlage."]
        return z

    z += ["", f"{'Block':14}{'Kauf':>7}{'Verkauf':>9}{'nichts':>8}{'Summe':>8}"]
    gesamt = 0
    for block, s in sorted(e["verteilung"].items(),
                           key=lambda x: -sum(x[1].values())):
        summe = sum(s.values())
        gesamt += summe
        z.append(f"{block:14}{s.get('kauf', 0):>7}{s.get('verkauf', 0):>9}"
                 f"{s.get('nichts', 0):>8}{summe:>8}")
    unbekannt = sum(e["verteilung"].get("unbekannt", {}).values())
    if gesamt:
        z += ["",
              f"Nicht zuordenbar: {unbekannt} von {gesamt} "
              f"({100.0 * unbekannt / gesamt:.0f} %)"]
        if unbekannt > 0.2 * gesamt:
            z.append("  ACHTUNG: ueber ein Fuenftel. Die Zuordnung ist "
                     "veraltet, nicht die Datenlage schlecht.")

    z += ["", "TRAGEN SIE SICH?"]
    aufgeloest = sum(a["aufgeloest"] for a in e["ausgang"].values())
    if not aufgeloest:
        z += ["  Noch kein Signal MIT Belegen ist aufgeloest.",
              "  Das ist die eigentliche Frage, und sie braucht Wochen -",
              "  bis dahin zaehlt dieses Skript die Verteilung, nicht den",
              "  Erfolg. Ein Skript, das den Unterschied verwischt, waere",
              "  schlimmer als keines."]
    else:
        z.append(f"  {'Block':14}{'aufgeloest':>12}{'Treffer':>9}{'Quote':>8}")
        for block, a in sorted(e["ausgang"].items(),
                               key=lambda x: -x[1]["aufgeloest"]):
            if not a["aufgeloest"]:
                continue
            q = 100.0 * a["treffer"] / a["aufgeloest"]
            z.append(f"  {block:14}{a['aufgeloest']:>12}{a['treffer']:>9}"
                     f"{q:>7.0f} %")
    return z


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    try:
        print("\n".join(bericht(messe(conn))))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
