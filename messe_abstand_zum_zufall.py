"""Schlaegt die LLM-Ebene den Zufall? Auf der groesstmoeglichen Stichprobe.

DIE FRAGE. Stehende Vorgabe vom 09.08.: *"die LLM-Loesung MUSS zwingend den
Zufall schlagen und messbar werden"*. Es gibt dazu bereits eine Funktion -
`compute_baseline_vergleich()`, gebaut am 29.07., **nie extern aufgerufen**.
Sie liefert fuer Hebel: 16,0 % Trefferquote gegen 33,3 % Breakeven, also
-17,3 pp bei p = 0,00026.

DREI VORBEHALTE GEGEN DIESE ZAHL, und dieses Skript raeumt alle drei aus.

1. SIE RUHT AUF 94 AUFGELOESTEN SIGNALEN - und die sind nicht repraesentativ.
   Verlierer laufen in den Stop und sind fertig; Gewinner bleiben offen stehen.
   Das ist die Aufloesungs-Asymmetrie (#617), und sie zieht die Quote nach
   UNTEN. Hier wird stattdessen der abgenommene Pfad-Bewerter benutzt: er
   bewertet auch unaufgeloeste Signale gegen den echten Kursverlauf und hebt
   die Stichprobe auf ueber 2.000.

2. SIE RECHNET MIT EINEM FESTEN BREAKEVEN VON 33,3 %. Das ist 1/(1+2,0), also
   die Mindestgrenze - nicht das tatsaechliche CRV. Der eigene Docstring sagt
   das ausdruecklich. Bei einem echten CRV von 3,0 liegt Breakeven bei 25,0 %,
   die Latte also 8 Punkte tiefer. Hier wird je Signal mit SEINEM CRV
   gerechnet.

3. SIE SAGT NICHTS UEBER DIE UNSICHERHEIT bei 17 bis 33 Symbolen. Ein
   Binomialtest unterstellt unabhaengige Ziehungen; 92 Signale auf 23 Symbolen
   sind das nicht (Methodik 2.5). Hier steht ein Cluster-Bootstrap ueber
   Symbole dahinter.

DREI POPULATIONEN, streng getrennt (dieselbe Trennung wie in Stufe 2):

    real             eine tatsaechliche Position - nur diese beantwortet
                     "wie gut ist das System"
    veto_schatten    das Gate hat gestoppt; kontrafaktisch
    halten_schatten  das Modell hat selbst gehalten; kontrafaktisch

UND ZWEI SICHTEN je Population, weil ihr Unterschied selbst ein Befund ist:

    nur aufgeloest   was die DB kennt - mit der Aufloesungs-Asymmetrie drin
    alle bewertbar   plus Mark-to-Market ueber den Pfad-Bewerter

Faellt die Quote von der zweiten zur ersten Sicht deutlich ab, ist der
Pessimismus der DB-Zahl belegt statt behauptet.

Aufruf:
    python messe_abstand_zum_zufall.py --db <kopie.db> [--horizont 14]
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
    _block_bootstrap_ziel_anteil,
    _tier_fuer_spot_symbol,
    _zonen_absolut,
    kumulative_inzidenz,
    lade_kursreihen,
    simuliere_signal,
)

_POPULATIONEN = (("real", "outcome_"), ("veto_schatten", "veto_outcome_"),
                 ("halten_schatten", "selbst_halten_outcome_"))


def _sammle(conn, horizont: int, kette: str = "rollen") -> list[dict]:
    """Signale einsammeln - AUF EINE KETTE BESCHRAENKT.

    ⚠️ DER FILTER FEHLTE BIS ZUM 25.08.2026, UND ER IST NICHT OPTIONAL.
    Dieses Skript entstand am 09.08., als es nur EINE Kette gab. Die
    Rollen-Kette kam am 12.-15.08. dazu - seither liegen in `signals` zwei
    Populationen nebeneinander:

        alte Kette / NULL   2.983
        quelle_kette=rollen 1.997
        hebel_signals       1.998   <- kennt die Spalte GAR NICHT, also alt

    Ungefiltert misst dieses Skript 4.981 alte gegen 1.997 neue Signale -
    also ueberwiegend die ALTE Kette, und das Ergebnis traegt trotzdem den
    Namen der neuen. Genau davor warnt `trefferbilanz.zaehle()` im eigenen
    Docstring: *"Sie in einen Topf zu werfen waere der klassische Fehler: die
    alte Kette hatte andere Fakten, andere Prompts und ein anderes
    Aktionsvokabular - ihre Quote sagt nichts ueber diese."*

    `kette`:
        "rollen"  nur die neue Kette (Vorgabe)
        "alt"     nur Zeilen ohne `quelle_kette` - inkl. aller hebel_signals
        "alle"    ausdruecklich beides, fuer einen bewussten Vergleich

    ⚠️ KEIN STILLER RUECKFALL. Eine Tabelle ohne die Spalte `quelle_kette`
    gehoert zur ALTEN Kette; bei `kette="rollen"` wird sie deshalb ganz
    uebersprungen und das GEMELDET, statt sie kommentarlos mitzunehmen."""
    reihen = lade_kursreihen(conn)
    from config import get_watchlist
    idx = _assetklasse_index(get_watchlist(), "messe_abstand_zum_zufall()")
    zeilen = []
    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        hat_kette = "quelle_kette" in spalten
        if kette == "rollen" and not hat_kette:
            print(f"  [uebersprungen] {tabelle}: keine Spalte `quelle_kette` "
                  f"-> gehoert zur alten Kette")
            continue
        if kette == "alt" and hat_kette:
            wo = "WHERE quelle_kette IS NULL"
        elif kette == "rollen":
            wo = "WHERE quelle_kette = 'rollen'"
        else:
            wo = ""
        n_tab = conn.execute(
            f"SELECT COUNT(*) FROM {tabelle} {wo}").fetchone()[0]
        print(f"  [{tabelle}] {n_tab} Zeilen fuer Kette '{kette}'")
        for row in conn.execute(f"SELECT * FROM {tabelle} {wo}"):
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
                population = name
                status = st
                db_r = row[f"{praefix}realisiertes_crv"]
                break
            if population is None:
                continue
            sim = simuliere_signal(z, reihe, str(row["created_at"])[:10], horizont,
                                   voller_horizont_noetig=False)
            if sim is None:
                continue
            aufgeloest = status in _RESOLVED_OUTCOMES and db_r is not None
            # Ereignisart fuer den Aalen-Johansen-Schaetzer. 'offen' des
            # Simulators heisst zensiert: bis zum Reihenende keine Barriere.
            art = {"ziel": "ziel", "stop": "stop"}.get(sim["ausgang"], "zensiert")
            zeilen.append({
                "tier": "hebel" if ist_hebel else _tier_fuer_spot_symbol(row["symbol"], idx),
                "symbol": row["symbol"], "population": population,
                "aufgeloest": aufgeloest,
                "r": db_r if aufgeloest else sim["r"],
                "tag": sim["tag"], "ausgang_art": art,
                "crv": z["crv"], "ist_short": z["ist_short"],
                "balken": sim.get("balkenabstand_median"),
            })
    return zeilen


def _auswerten(zeilen: list[dict], titel: str, horizont: int) -> None:
    """Zielquote per KONKURRIERENDE EREIGNISSE, nicht per r > 0.

    DER FEHLER, DEN DAS BEHEBT (gefunden 09.08. in der eigenen ersten Fassung).
    Ich hatte "Treffer" als `r > 0` definiert. Das ist bei einem zensierten
    Fall falsch: eine Position, die weder Ziel noch Stop getroffen hat und
    zufaellig bei +0,2 R steht, hat ihr Ziel NIE erreicht - sie ist nur noch
    nicht ausgestoppt. Gemessen an den echten Zahlen:

        echte Zieltreffer                       27
        zensiert, aber ueber Wasser (r > 0)     66   <- zaehlten faelschlich mit

    Damit sprang die "Trefferquote" der Hebel-real-Gruppe von 16 % auf 35 %,
    und der Abstand zum Zufall von -9,6 auf +8,4 pp. Beides war ein Artefakt
    der Barrieren-Konditionierung, vor der `basislinie_erwartungswert()` im
    eigenen Docstring warnt: was den Stop nicht trifft, ist nach oben
    selektiert.

    Der richtige Schaetzer steht seit dem 03.08. im Projekt und hatte hier
    seinen ersten Anwendungsfall: `kumulative_inzidenz()` (Aalen-Johansen).
    Er behandelt Ziel und Stop als konkurrierende Ereignisse mit
    Rechtszensierung - ein Signal mit 3 von 14 Tagen traegt zum Risikoset
    dieser 3 Tage bei, statt entweder als Verlierer gezaehlt oder weggeworfen
    zu werden.

    Das Vertrauensintervall kommt aus `_block_bootstrap_ziel_anteil()`, das
    ebenfalls schon existierte und ueber SYMBOLE zieht."""
    if not zeilen:
        print(f"  {titel:38} -")
        return
    ereignisse = [(z["tag"], z["ausgang_art"], z["symbol"]) for z in zeilen]
    inz = kumulative_inzidenz(ereignisse, horizont)
    quote = inz.get("ziel_anteil")
    # Breakeven je Signal gemittelt - die Latte, die diese Auswahl sich selbst
    # gesetzt hat.
    breakeven = statistics.mean(1.0 / (1.0 + z["crv"]) for z in zeilen)
    cu, co = _block_bootstrap_ziel_anteil(ereignisse, horizont)
    if quote is None:
        print(f"  {titel:38} n={len(zeilen):>5}  (keine Aufloesung im Horizont)")
        return
    abstand = (quote - breakeven) * 100.0
    if cu is None:
        ci, urteil = "-", ""
    else:
        cu_pp, co_pp = (cu - breakeven) * 100.0, (co - breakeven) * 100.0
        ci = f"[{cu_pp:+.1f}; {co_pp:+.1f}]"
        urteil = ("  SCHLAEGT den Zufall" if cu_pp > 0 else
                  ("  schlaegt ihn NICHT" if co_pp < 0 else "  nicht unterscheidbar"))
    art = Counter(z["ausgang_art"] for z in zeilen)
    print(f"  {titel:38} n={len(zeilen):>5}  Sym={len({z['symbol'] for z in zeilen}):>3}  "
          f"Ziel {quote:>6.1%}  Breakeven {breakeven:>6.1%}  "
          f"Abstand {abstand:>+6.1f} pp  {ci:>16}{urteil}")
    print(f"  {'':38} davon {art['ziel']} Ziel / {art['stop']} Stop / "
          f"{art['zensiert']} zensiert")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--horizont", type=int, default=14)
    # ⚠️ VORGABE IST DIE NEUE KETTE (25.08.2026). Wer die alte messen will,
    # sagt es ausdruecklich - nicht umgekehrt. Der stille Mischtopf war der
    # Zustand bis heute und haette die neue Kette mit 4.981 alten gegen 1.997
    # neue Signale gemessen.
    p.add_argument("--kette", choices=("rollen", "alt", "alle"),
                   default="rollen",
                   help="welche Signalkette gemessen wird (Vorgabe: rollen)")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    print(f"KETTE: {args.kette}")
    zeilen = _sammle(conn, args.horizont, args.kette)
    print(f"Bewertbare Zeilen: {len(zeilen)} (Horizont {args.horizont})")
    print(f"Verteilung: {dict(Counter(z['population'] for z in zeilen))}")
    print()
    print("MASSSTAB ist CRV-Breakeven 1/(1+CRV) JE SIGNAL, nicht der Muenzwurf.")
    print("Vertrauensbereich: Cluster-Bootstrap ueber SYMBOLE (Methodik 2.5).")
    print()

    for tier in sorted({z["tier"] for z in zeilen}):
        teil = [z for z in zeilen if z["tier"] == tier]
        if len(teil) < 10:
            continue
        print(f"=== {tier.upper()} ===")
        for population, _ in _POPULATIONEN:
            gruppe = [z for z in teil if z["population"] == population]
            if not gruppe:
                continue
            _auswerten(gruppe, f"{population}, alle bewertbar", args.horizont)
            _auswerten([z for z in gruppe if z["aufgeloest"]],
                       f"{population}, nur aufgeloest", args.horizont)
        # Nur dichte Kursreihen - die duennen reproduzieren schlechter.
        dicht = [z for z in teil if z["population"] == "real"
                 and (z["balken"] or 0) <= 1.5]
        _auswerten(dicht, "real, nur dichte Kursreihen", args.horizont)
        print()

    print("LESEART. Ein positiver Abstand heisst: die Auswahl erreicht ihre Ziele")
    print("oefter, als es ihr eigenes CRV verlangt - sie traegt. Null oder negativ")
    print("heisst: sie traegt nicht, unabhaengig davon wie die Trefferquote klingt.")
    print("Schliesst der Vertrauensbereich die Null ein, ist gar nichts gezeigt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
