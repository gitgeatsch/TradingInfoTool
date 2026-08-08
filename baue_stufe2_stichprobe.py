"""Stufe 2 der Fakten-Entscheidungsmappe Kapitel 9: die Stichprobe verbreitern.

WAS STUFE 2 WIRKLICH IST. Der Plan formuliert sie als *„der validierte Bewerter
ueber die unaufgeloesten Signale, hebt die Stichprobe von 92 auf potenziell
~1.400"*. Die Messung vor dem Bau zeigt: **ein grosser Teil dieser Hebung
existiert bereits in der Datenbank.** Zwei Schattenmessungen produzieren seit
dem 28.07. bzw. 31.07. genau solche kontrafaktischen Ausgaenge:

    veto_outcome_*          (28.07.)  Signale, die ein Risiko-Veto gestoppt hat
    selbst_halten_outcome_* (31.07.)  HALTEN, das vom Modell selbst kam

Stufe 2 ist deshalb NICHT „den Bewerter erstmals anwenden", sondern:

  1. die vier Populationen **zusammenfuehren, ohne sie zu vermischen**, und
  2. die noch OFFENEN Schattenfaelle per Mark-to-Market bewerten - das ist der
     Teil, den es wirklich noch nicht gibt.

VIER POPULATIONEN, DIE NIE IN EINE KENNZAHL GEHOEREN:

    real            eine tatsaechliche Position. Nur diese Gruppe beantwortet
                    "wie gut ist das System".
    veto_schatten   das Gate hat gestoppt. Kontrafaktisch: was WAERE passiert.
    halten_schatten das Modell hat selbst gehalten. Ebenfalls kontrafaktisch.
    unerfasst       traegt Zonen, wird aber von keiner Schattenmessung gefuehrt.

Die Trennung ist keine Formsache. Genau ihre Verletzung war der Fehler, den
`_SYSTEMGUETE_NUR_ECHTE_TRADES` am 03.08. behoben hat: HALTEN-Zeilen zaehlten
als „offene Trades" und drueckten die Aufloesungsquote von 26 % auf 3 %. Fuer
den Drei-Arm-Nachweis aus Stufe 3 sind die kontrafaktischen Gruppen dagegen
GENAU der Punkt - wenn Arm A haelt und Arm B eroeffnet, muss B bewertet werden.

ZWEI BEOBACHTUNGSREGIME, beide berichtet, weil beide etwas anderes koennen:

    gleiche Dauer  (voller_horizont_noetig=True)  jedes Signal bekommt exakt
                   `--horizont` Tage. Noetig, sobald R-Werte GEMITTELT werden -
                   sonst haetten aeltere Signale mehr Gelegenheit, ihren Stop
                   zu treffen (Kontrolle 1 aus Task #602).
    zensiert       (voller_horizont_noetig=False) nimmt auch teilbeobachtete
                   Faelle mit. Nur fuer Auswerter, die Rechtszensierung
                   beherrschen - `kumulative_inzidenz()` tut das.

BALKENDICHTE. Jede Zeile traegt `balkenabstand_median` mit. Auf Reihen groeber
als `_DICHT_GRENZE` reproduziert der Bewerter nachweislich schlechter (83,3 %
gegen 100,0 %, Abnahme 09.08.). Nutzer-Entscheidung: kennzeichnen statt
ausschliessen - die Faelle bleiben drin, die Auswertung berichtet getrennt.

DESKTOP-BETRIEB. Nur gegen eine KOPIE der Produktions-DB, reines Lesen.

Aufruf:
    python baue_stufe2_stichprobe.py --db <kopie.db> [--horizont 14] [--json raus.json]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict

from agent.krypto.backward_tracking import (
    OUTCOME_LIQUIDATION,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    _RESOLVED_OUTCOMES,
    _tier_fuer_spot_symbol,
    _assetklasse_index,
    _zonen_absolut,
    lade_kursreihen,
    simuliere_signal,
)

_DICHT_GRENZE = 1.5

# Leerlauf-Wache: unterhalb dieser Zahl ist die "verbreiterte Stichprobe" keine.
_MIND_ZEILEN = 500

# Welche Spaltenpraefixe gehoeren zu welcher Population?
_POPULATIONEN = (
    ("real", "outcome_"),
    ("veto_schatten", "veto_outcome_"),
    ("halten_schatten", "selbst_halten_outcome_"),
)


def _status_und_r(row, praefix: str, spalten: set[str]):
    """(status, r) einer Population, oder (None, None) wenn es sie nicht gibt."""
    s_sp, r_sp = f"{praefix}status", f"{praefix}realisiertes_crv"
    if s_sp not in spalten:
        return None, None
    return row[s_sp], (row[r_sp] if r_sp in spalten else None)


def _sammle(conn, horizont: int) -> list[dict]:
    reihen = lade_kursreihen(conn)
    # Die Watchlist MUSS geladen werden. Ohne sie landen Krypto, Aktien,
    # Rohstoffe und Themen-ETF in einem Sammel-Topf 'spot' - genau der Fehler
    # vom 29.07., gegen den _assetklasse_index() seither laut warnt. Ein
    # Mischtopf sieht aus wie eine Kennzahl und ist keine.
    from config import get_watchlist
    idx = _assetklasse_index(get_watchlist(), "baue_stufe2_stichprobe()")

    zeilen: list[dict] = []
    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        for row in conn.execute(f"SELECT * FROM {tabelle}"):
            z = _zonen_absolut(row)
            if z is None:
                continue
            reihe = reihen.get(row["symbol"])
            if not reihe:
                continue

            # Zu welcher Population gehoert die Zeile? Die erste, die einen
            # Status fuehrt, gewinnt - 'real' zuerst, weil eine echte Position
            # nie als Schatten gezaehlt werden darf.
            population, status, db_r = "unerfasst", None, None
            for name, praefix in _POPULATIONEN:
                st, rr = _status_und_r(row, praefix, spalten)
                if st is None:
                    continue
                if name == "real" and st == "nicht_anwendbar":
                    # HALTEN: war nie ein Trade. Weitersuchen, ob eine
                    # Schattenmessung sie fuehrt.
                    continue
                population, status, db_r = name, st, rr
                break

            start = str(row["created_at"])[:10]
            sim_gleich = simuliere_signal(z, reihe, start, horizont,
                                          voller_horizont_noetig=True)
            sim_zens = simuliere_signal(z, reihe, start, horizont,
                                        voller_horizont_noetig=False)
            if sim_zens is None:
                continue

            aufgeloest = status in _RESOLVED_OUTCOMES
            zeilen.append({
                "tabelle": tabelle,
                "id": row["id"],
                "symbol": row["symbol"],
                "tier": "hebel" if ist_hebel else _tier_fuer_spot_symbol(row["symbol"], idx),
                "created_at": str(row["created_at"])[:10],
                "population": population,
                "db_status": status,
                # Der DB-Wert hat Vorrang, wo es ihn gibt - er ist das
                # tatsaechliche Ergebnis, nicht die Nachbildung.
                "r": db_r if (aufgeloest and db_r is not None) else (
                    sim_gleich["r"] if sim_gleich else None),
                "r_quelle": "db" if (aufgeloest and db_r is not None) else (
                    "mark_to_market" if sim_gleich else None),
                "r_zensiert": sim_zens["r"],
                "ausgang_zensiert": sim_zens["ausgang"],
                "ist_zensiert": bool(sim_zens["zensiert"]),
                "tag": sim_zens["tag"],
                "balkenabstand_median": sim_zens.get("balkenabstand_median"),
                "stop_rel": z["stop_rel"],
                "crv": z["crv"],
                "ist_short": z["ist_short"],
            })
    return zeilen


def _tabelle(titel: str, gruppen: dict[str, list[float]]) -> None:
    print(f"  {titel}")
    print(f"    {'Population':18} {'n':>6} {'Mittel R':>10} {'Median R':>10}")
    for name in ("real", "veto_schatten", "halten_schatten", "unerfasst"):
        w = gruppen.get(name) or []
        if not w:
            print(f"    {name:18} {0:>6} {'-':>10} {'-':>10}")
            continue
        print(f"    {name:18} {len(w):>6} {statistics.mean(w):>10.3f} "
              f"{statistics.median(w):>10.3f}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="Pfad zur KOPIE der Produktions-DB")
    p.add_argument("--horizont", type=int, default=14)
    p.add_argument("--json", help="Datensatz zusaetzlich als JSON schreiben")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    zeilen = _sammle(conn, args.horizont)
    if len(zeilen) < _MIND_ZEILEN:
        print(f"ABBRUCH (Leerlauf-Wache): nur {len(zeilen)} bewertbare Zeilen, "
              f"noetig sind {_MIND_ZEILEN}.")
        return 2

    print(f"Bewertbare Zeilen (Zonen + Kursreihe): {len(zeilen)}")
    print(f"Horizont fuer gleiche Beobachtungsdauer: {args.horizont} Tage")
    print()

    nach_pop = Counter(z["population"] for z in zeilen)
    nach_quelle = Counter(z["r_quelle"] for z in zeilen)
    print("=== HERKUNFT DES R-WERTS ===")
    for pop in ("real", "veto_schatten", "halten_schatten", "unerfasst"):
        c = Counter(z["r_quelle"] for z in zeilen if z["population"] == pop)
        print(f"  {pop:18} gesamt {nach_pop[pop]:>5}   "
              f"aus DB {c['db']:>5}   Mark-to-Market {c['mark_to_market']:>5}   "
              f"ohne Wert {c[None]:>5}")
    print(f"  {'SUMME':18} gesamt {len(zeilen):>5}   "
          f"aus DB {nach_quelle['db']:>5}   Mark-to-Market {nach_quelle['mark_to_market']:>5}   "
          f"ohne Wert {nach_quelle[None]:>5}")
    print()

    print("=== R-WERTE, GLEICHE BEOBACHTUNGSDAUER (mittelbar) ===")
    g = defaultdict(list)
    for z in zeilen:
        if z["r"] is not None:
            g[z["population"]].append(z["r"])
    _tabelle(f"alle Balkendichten", g)
    print()
    gd = defaultdict(list)
    for z in zeilen:
        if z["r"] is None:
            continue
        if (z["balkenabstand_median"] or 0) <= _DICHT_GRENZE:
            gd[z["population"]].append(z["r"])
    _tabelle(f"nur dichte Kursreihen (<= {_DICHT_GRENZE} Tage)", gd)
    print()

    duenn = sum(1 for z in zeilen
                if (z["balkenabstand_median"] or 0) > _DICHT_GRENZE)
    zens = sum(1 for z in zeilen if z["ist_zensiert"])
    print("=== KENNZEICHNUNG ===")
    print(f"  auf duennen Kursreihen: {duenn} ({duenn / len(zeilen):.1%})")
    print(f"  zensiert (keine Barriere bis Reihenende): {zens} "
          f"({zens / len(zeilen):.1%})")
    print()

    print("=== JE TIER (nur echte Trades) ===")
    t = defaultdict(list)
    for z in zeilen:
        if z["population"] == "real" and z["r"] is not None:
            t[z["tier"]].append(z["r"])
    for tier in sorted(t):
        w = t[tier]
        print(f"  {tier:12} n={len(w):>5}  Mittel {statistics.mean(w):>7.3f} R")

    # Ausreisser benennen, statt sie im Mittelwert verschwinden zu lassen. Ein
    # einzelner R-Wert jenseits von |5| ist bei einem CRV um 2-3 arithmetisch
    # kaum erreichbar und deutet auf einen Datenfehler - so wurde am 06.08. der
    # ETC-Instrumenten-Verwechsler gefunden.
    grob = sorted((z for z in zeilen if z["r"] is not None and abs(z["r"]) > 5.0),
                  key=lambda z: -abs(z["r"]))
    if grob:
        print()
        print(f"=== VERDAECHTIGE R-WERTE (|R| > 5) — {len(grob)} Stueck ===")
        for z in grob[:10]:
            print(f"  {z['tabelle']:14} id={z['id']:<6} {z['symbol']:<8} "
                  f"{z['population']:16} R={z['r']:>8.2f}  CRV={z['crv']:.2f}  "
                  f"Quelle={z['r_quelle']}")
        print("  Ein |R| deutlich ueber dem CRV ist arithmetisch nicht "
              "erreichbar und zeigt einen Datenfehler an, keine Leistung.")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(zeilen, f, ensure_ascii=False)
        print(f"\nDatensatz geschrieben: {args.json} ({len(zeilen)} Zeilen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
