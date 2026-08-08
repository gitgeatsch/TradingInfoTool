"""Abnahmekriterium fuer den Pfad-Bewerter - Fakten-Entscheidungsmappe Kapitel 9, Stufe 1.

WARUM ES DIESES SKRIPT GIBT. `simuliere_signal()` bewertet ein Signal gegen die
Kurshistorie und liefert einen R-Wert. Er ist seit dem 03.08. NICHT nur ein
Analysewerkzeug, sondern speist ueber `_SYSTEMGUETE_MARK_TO_MARKET` die
produktive Systemguete: unaufgeloeste Signale werden damit mark-to-market
bewertet (Export 09.08.: 39 von 133 Faellen bei hebel/real). Geprueft wurde er
nie. Kapitel 9 formuliert das Abnahmekriterium:

    "Er muss die bekannten Ausgaenge reproduzieren. Reproduziert er sie nicht,
     ist er fuer die anderen ~1.400 nicht vertrauenswuerdig."

Genau das misst dieses Skript.

WAS VERGLICHEN WIRD. Fuer jede aufgeloeste Zeile (`_RESOLVED_OUTCOMES`) mit
vollstaendigen Zonen und Kursreihe wird der Bewerter ab `created_at` laufen
gelassen und sein `ausgang` gegen `outcome_status` gehalten, sein `r` gegen
`outcome_realisiertes_crv`.

ZWEI BEKANNTE KONSTRUKTIONSUNTERSCHIEDE, die dieser Test sichtbar machen soll -
sie sind der Grund, warum er nicht trivial bestehen muss:

1. RICHTUNGSHERLEITUNG. `check_signal_outcome()` (der Live-Tracker) leitet die
   Richtung aus der `action` ab (`richtung_aus_action`), `_zonen_absolut()` aus
   der Lage der Zonen (`ziel < entry` = short). Bei einem Signal, dessen Zonen
   der action widersprechen, urteilen beide verschieden.
2. ZONENKANTE. Der Live-Tracker nimmt ueber `_threshold()` die `_von`-Kante fuer
   BEIDE Richtungen, `_zonen_absolut()` spiegelt bei short auf die `_bis`-Kante.

KONTROLLEN (Methodik-Nachtrag 09.08., Punkte 5 und 7):

- NEGATIVKONTROLLE: derselbe Lauf, aber ab einem um `_KONTROLLE_VERSATZ_TAGE`
  frueheren Startdatum - dieselben Zonen gegen einen unbeteiligten Abschnitt
  DERSELBEN Kursreihe. Bricht die Uebereinstimmung dabei NICHT ein, misst der
  Test nichts und sein positives Ergebnis ist wertlos.

  VERWORFENE ERSTE FASSUNG (09.08., dokumentiert weil lehrreich): zuerst wurden
  Stop und Ziel VERTAUSCHT. Das ergab 83,0 % gegen 91,5 % - scheinbar ein
  Einbruch, tatsaechlich ein Artefakt. Beim Tausch liegt der "Stop" eines LONG
  ueber dem Einstieg und wird am ersten Tag getroffen; da 87 der 106 bekannten
  Ausgaenge `stop_loss_erreicht` lauten, stimmte die kaputte Variante aus dem
  falschen Grund zu. Eine Kontrolle, die aus Versehen richtig liegt, ist keine.
- LEERLAUF-WACHE: unter `_MIND_FAELLE` auswertbaren Faellen bricht das Skript
  ab, statt "100 % Uebereinstimmung" auf drei Zeilen zu melden.
- UNGEMESSEN != WIDERLEGT: Zeilen ohne Kursreihe, ohne Zonen, mit ausgeloester
  Plausibilitaetsschranke ODER mit ZENSIERTEM Ergebnis werden getrennt
  ausgewiesen und gehen in KEINE Quote ein. (Methodik-Nachtrag 09.08., Punkt 3.)

  Die Zensierung gehoert ausdruecklich hierher: `zensiert=True` heisst, dass die
  vorliegende OHLC-Reihe bis zu ihrem Ende KEINE Barriere zeigt. Das ist ein
  Datenbefund - der Bewerter sieht den Zeitraum nicht, den der Live-Tracker
  gesehen hat (der zieht auch `price_cache`, nicht nur Tageskerzen). Es ist kein
  Widerspruch zum DB-Ergebnis und darf nicht als Reproduktionsfehler zaehlen.
  Eine hohe Zensurquote ist trotzdem ein eigenes Ergebnis und wird berichtet.

DESKTOP-BETRIEB. Laeuft ausschliesslich gegen eine KOPIE der Produktions-DB
(`--db`), nie gegen eine laufende Instanz. Reines Lesen, keine Schreibpfade.

Aufruf:
    python pruefe_pfad_bewerter.py --db <pfad/zur/kopie.db>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import Counter

from agent.krypto.backward_tracking import (
    OUTCOME_LIQUIDATION,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    _RESOLVED_OUTCOMES,
    _zonen_absolut,
    lade_kursreihen,
    simuliere_signal,
)

# Wie weit darf der Bewerter laufen? Bewusst grosszuegig ueber dem laengsten
# Ablauf-Bucket (120 Tage): eine aufgeloeste Zeile HAT ihre Barriere innerhalb
# ihres Buckets getroffen, ein groesseres Fenster kann das Ergebnis also nicht
# verfaelschen - es verhindert nur, dass der Vergleich an der Fensterlaenge
# scheitert statt an der Sache.
_HORIZONT_TAGE = 200

# Leerlauf-Wache. Kapitel 9 nennt 92 bekannte Ausgaenge; darunter ist die
# Aussage keine.
_MIND_FAELLE = 40

# Ab welcher absoluten Abweichung gilt der R-Wert als verschieden? Der
# Live-Tracker und der Bewerter runden an verschiedenen Stellen; 0,05 R ist
# klein gegenueber jedem Effekt, um den es hier geht.
_R_TOLERANZ = 0.05

# Negativkontrolle: um wie viele Tage wird der Start nach hinten verschoben?
# 180 Tage sind weit genug, dass der gepruefte Kursabschnitt mit dem echten
# nichts mehr zu tun hat, und nah genug, dass die Preisskala vergleichbar
# bleibt - sonst wuerde die Plausibilitaetsschranke die Kontrolle leerlaufen
# lassen, statt sie scheitern zu lassen.
_KONTROLLE_VERSATZ_TAGE = 180

# Bis zu welchem Median-Balkenabstand gilt eine Reihe als dicht genug, damit
# "Stop schlaegt Ziel am selben Tag" eine konservative Konvention bleibt statt
# eines Muenzwurfs? 1,5 Tage laesst Wochenendluecken der Boersenwerte durch und
# trennt sie sauber von den 4-Tage-Reihen. Siehe
# backward_tracking._balkenabstand_median().
_DICHT_GRENZE = 1.5

_AUSGANG_ZU_STATUS = {
    "ziel": OUTCOME_TAKE_PROFIT,
    "stop": OUTCOME_STOP_LOSS,
}


def _lade_faelle(conn) -> list[dict]:
    """Alle aufgeloesten Zeilen beider Tabellen mit ihren Zonen.

    Laedt die echten DB-Zeilen, statt sie nachzubauen - eine nachgebaute Zeile
    beweist nur, dass der Nachbau zum Bewerter passt.
    """
    faelle: list[dict] = []
    platzhalter = ",".join("?" for _ in _RESOLVED_OUTCOMES)
    for tabelle in ("signals", "hebel_signals"):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        gewuenscht = [
            "id", "symbol", "created_at", "action", "outcome_status",
            "outcome_realisiertes_crv", "outcome_entschieden_am",
            "entry_usd_von", "entry_usd_bis", "entry_usd",
            "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_usd",
            "take_profit_usd_von", "take_profit_usd_bis", "take_profit_usd",
        ]
        felder = [c for c in gewuenscht if c in spalten]
        rows = conn.execute(
            f"SELECT {', '.join(felder)} FROM {tabelle} "
            f"WHERE outcome_status IN ({platzhalter})",
            _RESOLVED_OUTCOMES,
        ).fetchall()
        for row in rows:
            faelle.append({"tabelle": tabelle, "row": row})
    return faelle


def _versetztes_datum(iso_tag: str, tage: int) -> str:
    from datetime import date, timedelta
    j, m, t = (int(x) for x in iso_tag.split("-"))
    return (date(j, m, t) - timedelta(days=tage)).isoformat()


def _bewerte(faelle: list[dict], reihen: dict, kaputt: bool) -> dict:
    """Ein Durchlauf. `kaputt=True` startet `_KONTROLLE_VERSATZ_TAGE` frueher."""
    ergebnis = {
        "uebereinstimmung": 0,
        "abweichung": 0,
        "ungemessen": Counter(),
        "r_gleich": 0,
        "r_verschieden": 0,
        "abweichungen": [],
        "dicht": {"n": 0, "treffer": 0},
        "duenn": {"n": 0, "treffer": 0},
    }
    for fall in faelle:
        row = fall["row"]
        z = _zonen_absolut(row)
        if z is None:
            ergebnis["ungemessen"]["keine_zonen"] += 1
            continue
        reihe = reihen.get(row["symbol"])
        if not reihe:
            ergebnis["ungemessen"]["keine_kursreihe"] += 1
            continue

        start = str(row["created_at"])[:10]
        if kaputt:
            start = _versetztes_datum(start, _KONTROLLE_VERSATZ_TAGE)

        sim = simuliere_signal(
            z, reihe, start, _HORIZONT_TAGE, voller_horizont_noetig=False,
        )
        if sim is None:
            ergebnis["ungemessen"]["bewerter_gibt_none"] += 1
            continue
        if sim.get("zensiert"):
            # Keine Barriere bis zum Ende der vorliegenden Reihe. Datenlage,
            # kein Widerspruch - siehe Modul-Docstring, Kontrollen.
            ergebnis["ungemessen"]["zensiert_keine_barriere"] += 1
            continue

        erwartet = row["outcome_status"]
        # 'liquidation_wahrscheinlich' ist der Hebel-Sonderfall eines
        # Stop-Ereignisses - der Bewerter kennt nur die Barriere selbst.
        if erwartet == OUTCOME_LIQUIDATION:
            erwartet = OUTCOME_STOP_LOSS
        tatsaechlich = _AUSGANG_ZU_STATUS.get(sim["ausgang"])

        # Getrennt nach Balkendichte berichten (Nutzer-Entscheidung 09.08.:
        # kennzeichnen statt ausschliessen). Oberhalb von _DICHT_GRENZE ist die
        # Konvention "Stop schlaegt Ziel" nicht mehr konservativ, sondern
        # willkuerlich - eine gemeinsame Quote wuerde beide Populationen
        # vermischen und die gute schoenrechnen.
        dicht = (sim.get("balkenabstand_median") or 0) <= _DICHT_GRENZE
        ergebnis["dicht" if dicht else "duenn"]["n"] += 1

        if tatsaechlich == erwartet:
            ergebnis["dicht" if dicht else "duenn"]["treffer"] += 1
            ergebnis["uebereinstimmung"] += 1
            db_r = row["outcome_realisiertes_crv"]
            if db_r is not None and sim["r"] is not None:
                if abs(db_r - sim["r"]) <= _R_TOLERANZ:
                    ergebnis["r_gleich"] += 1
                else:
                    ergebnis["r_verschieden"] += 1
        else:
            ergebnis["abweichung"] += 1
            if len(ergebnis["abweichungen"]) < 15:
                ergebnis["abweichungen"].append({
                    "tabelle": fall["tabelle"],
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "action": row["action"] if "action" in row.keys() else None,
                    "db_status": row["outcome_status"],
                    "sim_ausgang": sim["ausgang"],
                    "sim_zensiert": sim.get("zensiert"),
                    "db_r": row["outcome_realisiertes_crv"],
                    "sim_r": sim["r"],
                    "ist_short_laut_zonen": z["ist_short"],
                })
    return ergebnis


def _quote(e: dict) -> float | None:
    n = e["uebereinstimmung"] + e["abweichung"]
    return None if n == 0 else e["uebereinstimmung"] / n


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="Pfad zur KOPIE der Produktions-DB")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    faelle = _lade_faelle(conn)
    reihen = lade_kursreihen(conn)
    print(f"Aufgeloeste Zeilen gesamt: {len(faelle)}")
    print(f"Symbole mit Kursreihe:     {len(reihen)}")
    print()

    echt = _bewerte(faelle, reihen, kaputt=False)
    n_bewertbar = echt["uebereinstimmung"] + echt["abweichung"]

    if n_bewertbar < _MIND_FAELLE:
        print(f"ABBRUCH (Leerlauf-Wache): nur {n_bewertbar} auswertbare Faelle, "
              f"noetig sind {_MIND_FAELLE}.")
        print(f"  ungemessen: {dict(echt['ungemessen'])}")
        return 2

    kontrolle = _bewerte(faelle, reihen, kaputt=True)

    q_echt, q_kontrolle = _quote(echt), _quote(kontrolle)
    print("=== ECHTER LAUF ===")
    print(f"  auswertbar:       {n_bewertbar}")
    print(f"  Uebereinstimmung: {echt['uebereinstimmung']}  ({q_echt:.1%})")
    print(f"  Abweichung:       {echt['abweichung']}")
    print(f"  R-Wert gleich:    {echt['r_gleich']} von "
          f"{echt['r_gleich'] + echt['r_verschieden']} vergleichbaren")
    print(f"  ungemessen:       {dict(echt['ungemessen'])}")
    print()
    print(f"  nach Balkendichte (Grenze {_DICHT_GRENZE} Tage):")
    for label, key in (("dicht", "dicht"), ("duenn", "duenn")):
        g = echt[key]
        anteil = f"{g['treffer'] / g['n']:.1%}" if g["n"] else "-"
        print(f"    {label:6} n={g['n']:<4} reproduziert {g['treffer']:<4} ({anteil})")
    print()
    print(f"=== NEGATIVKONTROLLE (Start {_KONTROLLE_VERSATZ_TAGE} Tage frueher) ===")
    print(f"  Uebereinstimmung: {kontrolle['uebereinstimmung']}  "
          f"({q_kontrolle:.1%})" if q_kontrolle is not None else "  keine")
    print()

    if q_kontrolle is not None and q_kontrolle >= q_echt:
        print("KONTROLLE GESCHEITERT: die kaputte Variante ist nicht schlechter "
              "als die echte. Der Test misst nichts - das Ergebnis oben ist "
              "nicht verwertbar.")
        return 3

    print("=== ABWEICHUNGEN (erste 15) ===")
    for a in echt["abweichungen"]:
        print(f"  {a['tabelle']:14} id={a['id']:<6} {a['symbol']:<8} "
              f"action={str(a['action']):<12} db={a['db_status']:<22} "
              f"sim={a['sim_ausgang']:<6} zensiert={a['sim_zensiert']} "
              f"db_r={a['db_r']} sim_r={None if a['sim_r'] is None else round(a['sim_r'], 3)} "
              f"short_laut_zonen={a['ist_short_laut_zonen']}")
    if not echt["abweichungen"]:
        print("  keine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
