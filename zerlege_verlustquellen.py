"""Wo sitzt der Verlust? Zerlegung nach Ebenen, ohne einen LLM-Aufruf.

DIE FRAGE, praezise gestellt (Nutzer-Vorgabe 09.08.): *"der Test soll uns sagen
wo unsere Probleme liegen und was zu tun ist"*. Dass die LLM-Ebene den Zufall
nicht schlaegt, ist bekannt und keine Handlungsanweisung. Die Handlungsanweisung
entsteht erst, wenn man weiss, WELCHE Ebene wie viel kostet.

FUENF EBENEN, in der Reihenfolge, in der ein Signal sie durchlaeuft:

    1 SCREENING     welches Symbol wird ueberhaupt angesehen?
                    Fehlerbild: der Trigger feuert, der Kurs reagiert nie.
                    Messbar am MFE - laeuft der Kurs UEBERHAUPT in die
                    gedachte Richtung?
    2 RICHTUNG      LONG oder SHORT?
                    Fehlerbild: der Kurs laeuft von Anfang an dagegen.
                    Messbar an MFE < 0,25 R.
    3 STOP-ABSTAND  wie viel Luft bekommt die These?
                    Fehlerbild: knapp daneben ausgestoppt, danach lief es.
                    Messbar an 0,25 R <= MFE < 1 R.
    4 AUSSTIEG      wann wird realisiert?
                    Fehlerbild: die These stimmte, das Ziel wurde nie
                    mitgenommen. Messbar an MFE >= 1 R bei Verlust.
    5 GATE          was haelt das Veto zurueck, und was kostet es?
                    Messbar am Vergleich real gegen Veto-Schatten.

WARUM DAS MFE DER RICHTIGE SCHLUESSEL IST. Es beantwortet nicht "hat gewonnen",
sondern "wie weit lief es zu unseren Gunsten, bevor es scheiterte" (Sweeney
1996, MFE/MAE-Analyse). Genau diese Frage trennt die Ebenen: ein Trade, der nie
0,25 R erreicht, hat ein RICHTUNGS-Problem; einer, der 1,5 R erreicht und
trotzdem im Minus endet, ein AUSSTIEGS-Problem. Dieselbe Zerlegung wurde am
09.08. schon einmal auf 77 aufgeloeste Faelle angewandt; hier laeuft sie ueber
die volle bewertbare Menge.

WICHTIGE EINSCHRAENKUNG, die ins Ergebnis gehoert. Diese Zerlegung ist eine
DIAGNOSE, kein Plan. "40 % erreichten 1 R" heisst NICHT "40 % sind einholbar" -
der naheliegende Griff (Breakeven-Lock) wurde am 01.08. geprueft und verworfen,
weil er 63 % der Gewinner kostete. Jede Ausstiegsregel muss auf BEIDEN Seiten
gemessen werden.

    python zerlege_verlustquellen.py --db <kopie.db> [--horizont 14]
"""
from __future__ import annotations

import argparse
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict

from agent.krypto.backward_tracking import (
    _RESOLVED_OUTCOMES,
    _assetklasse_index,
    _tier_fuer_spot_symbol,
    _zonen_absolut,
    lade_kursreihen,
    simuliere_signal,
)

_POPULATIONEN = (("real", "outcome_"), ("veto_schatten", "veto_outcome_"),
                 ("halten_schatten", "selbst_halten_outcome_"))


def _mfe(z: dict, reihe: list, ab: str, horizont: int) -> float | None:
    """Hoechstes zu unseren Gunsten erreichtes R, unabhaengig vom Ausgang."""
    tage = [p for p in reihe if p["date"] >= ab][:horizont + 1]
    if not tage:
        return None
    bestes = None
    for p in tage:
        guenstig = p["low"] if z["ist_short"] else p["high"]
        if guenstig is None:
            continue
        r = ((z["entry"] - guenstig) if z["ist_short"]
             else (guenstig - z["entry"])) / z["risiko"]
        if bestes is None or r > bestes:
            bestes = r
    return bestes


def _sammle(conn, horizont: int) -> list[dict]:
    reihen = lade_kursreihen(conn)
    from config import get_watchlist
    idx = _assetklasse_index(get_watchlist(), "zerlege_verlustquellen()")
    zeilen = []
    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        for row in conn.execute(f"SELECT * FROM {tabelle}"):
            z = _zonen_absolut(row)
            if z is None:
                continue
            reihe = reihen.get(row["symbol"])
            if not reihe:
                continue
            population = status = db_r = None
            for name, praefix in _POPULATIONEN:
                if f"{praefix}status" not in spalten:
                    continue
                st = row[f"{praefix}status"]
                if st is None or (name == "real" and st == "nicht_anwendbar"):
                    continue
                population, status = name, st
                db_r = row[f"{praefix}realisiertes_crv"]
                break
            if population is None:
                continue
            ab = str(row["created_at"])[:10]
            sim = simuliere_signal(z, reihe, ab, horizont, voller_horizont_noetig=False)
            if sim is None:
                continue
            mfe = _mfe(z, reihe, ab, horizont)
            if mfe is None:
                continue
            aufgeloest = status in _RESOLVED_OUTCOMES and db_r is not None
            zeilen.append({
                "tier": "hebel" if ist_hebel else _tier_fuer_spot_symbol(row["symbol"], idx),
                "symbol": row["symbol"], "population": population,
                "r": db_r if aufgeloest else sim["r"], "mfe": mfe,
                "crv": z["crv"], "stop_rel": z["stop_rel"],
                "ausgang": sim["ausgang"], "ist_short": z["ist_short"],
            })
    return zeilen


def _ebene(mfe: float, crv: float) -> str:
    """Welche Ebene ist bei diesem Verlust zustaendig?"""
    if mfe < 0.25:
        return "2 RICHTUNG"
    if mfe < 1.0:
        return "3 STOP-ABSTAND"
    if mfe < crv:
        return "4 AUSSTIEG (1R erreicht, Ziel nicht)"
    return "4 AUSSTIEG (Ziel erreicht, nicht mitgenommen)"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--horizont", type=int, default=14)
    p.add_argument("--tier", default="hebel")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    alle = _sammle(conn, args.horizont)
    zeilen = [z for z in alle if z["tier"] == args.tier and z["population"] == "real"]
    if len(zeilen) < 20:
        print(f"Zu wenige Faelle fuer {args.tier}/real: {len(zeilen)}")
        return 2

    print(f"EBENEN-ZERLEGUNG  {args.tier}/real, Horizont {args.horizont}")
    print(f"Bewertbare Faelle: {len(zeilen)}, Symbole "
          f"{len({z['symbol'] for z in zeilen})}")
    print()

    verluste = [z for z in zeilen if z["r"] <= 0]
    gewinne = [z for z in zeilen if z["r"] > 0]
    print(f"  Gewinne {len(gewinne):4}   Verluste {len(verluste):4}   "
          f"Summe R {sum(z['r'] for z in zeilen):+.1f}")
    print()

    print("=== WO ENTSTEHEN DIE VERLUSTE? ===")
    nach_ebene = Counter(_ebene(z["mfe"], z["crv"]) for z in verluste)
    beitrag = defaultdict(float)
    for z in verluste:
        beitrag[_ebene(z["mfe"], z["crv"])] += z["r"]
    for e in sorted(nach_ebene):
        n = nach_ebene[e]
        print(f"  {e:40} {n:4}  {n/len(verluste):5.1%}   "
              f"Beitrag {beitrag[e]:+7.1f} R")
    print()

    print("=== EBENE 1: SCREENING - Symbole, deren Kurs nie reagiert ===")
    je_symbol = defaultdict(list)
    for z in zeilen:
        je_symbol[z["symbol"]].append(z)
    kandidaten = []
    for s, gruppe in je_symbol.items():
        if len(gruppe) < 4:
            continue
        med = statistics.median(g["mfe"] for g in gruppe)
        kandidaten.append((med, s, len(gruppe), sum(g["r"] for g in gruppe)))
    for med, s, n, summe in sorted(kandidaten)[:6]:
        marke = "   <-- Trigger feuert, Kurs reagiert nicht" if med < 0.25 else ""
        print(f"  {s:9} n={n:3}  Median-MFE {med:+5.2f} R  "
              f"Beitrag {summe:+7.1f} R{marke}")
    print()

    print("=== EBENE 5: GATE - was haelt es zurueck? ===")
    for population in ("real", "veto_schatten"):
        g = [z for z in alle if z["tier"] == args.tier and z["population"] == population]
        if not g:
            continue
        ziel = sum(1 for z in g if z["ausgang"] == "ziel")
        stop = sum(1 for z in g if z["ausgang"] == "stop")
        print(f"  {population:16} n={len(g):5}  Ziel {ziel:4}  Stop {stop:4}  "
              f"Mittel R {statistics.mean(z['r'] for z in g):+6.3f}  "
              f"Median MFE {statistics.median(z['mfe'] for z in g):+5.2f} R")
    print()

    print("=== WAS DARAUS FOLGT ===")
    groesste = max(beitrag.items(), key=lambda x: -x[1]) if beitrag else None
    if groesste:
        print(f"  Groesster Verlustbeitrag: {groesste[0]} mit {groesste[1]:+.1f} R")
    print("  ACHTUNG: das ist eine DIAGNOSE, kein Plan. '1R erreicht' heisst")
    print("  nicht 'einholbar' - der Breakeven-Lock wurde am 01.08. geprueft und")
    print("  verworfen, weil er 63 % der Gewinner kostete. Jede Ausstiegsregel")
    print("  muss auf BEIDEN Seiten gemessen werden: was sie rettet UND was sie")
    print("  kostet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
