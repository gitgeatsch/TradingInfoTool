# -*- coding: utf-8 -*-
"""Steigt die Handlungsquote mit der Zahl unabhaengiger Faktoren?

DIE HYPOTHESE (Faktenmappe 12.3). Der Fachstandard verlangt drei bis vier
UNABHAENGIGE Faktoren fuer einen tragfaehigen Einstieg. Unsere Eingabe liefert
zwei - Preis und Umsatz -, denn Struktur, Kursentwicklung und Niveaus stammen
alle aus derselben Kerzenreihe. Aus acht Durchlaeufen:

    Faktoren = 3   ->  beide Faelle gehandelt
    Faktoren = 2   ->  5x NICHTS_TUN, 1x REDUZIEREN

Falls das traegt, ist der Deadloop keine Fehlfunktion, sondern das System, das
den Standard korrekt auf eine unzureichende Eingabe anwendet. Acht Faelle sind
dafuer zu wenig. Dieses Skript macht daraus eine Zahl.

WAS GEMESSEN WIRD, und nur das: der Zusammenhang zwischen der vom Modell selbst
gezaehlten Faktorzahl und seiner Handlung. NICHT, ob die Handlung richtig war -
das ist eine andere Frage, und sie ist nach Arbeitsstand 7.25 ohnehin anders zu
stellen.

DIE ANKER kommen aus `ankerpopulation.json` - geschichtet nach
EINGANGSMERKMALEN, nicht nach Ausgang. Damit misst dieser Lauf nicht dieselbe
Verzerrung wie die acht Anker aus 7.8.

EINE DATENQUELLE, NICHT ZWEI. `pruefe_rollenkette` liest Bestand und Kurse ueber
seine Modulkonstante DB - standardmaessig die Desktop-Datenbank, deren Daten am
19.07. enden. Die Ankerpopulation stammt aber aus dem Notebook-Snapshot. Zwei
Datenstaende in einem Lauf waeren ein Konstruktionsfehler der Sorte, die dieses
Projekt teuer bezahlt hat: die Indizes zeigten auf andere Tage. Deshalb wird die
Konstante hier explizit umgebogen, und der verwendete Stand steht im Kopf der
Ausgabe.

    python messe_faktorzahl.py --db <pfad> --trocken     Vorflug, 0 Aufrufe
    python messe_faktorzahl.py --db <pfad>               der Lauf
"""
# GESTRICHEN AM 12.08. (L1). Dieses Skript rief `beschreibe_marktbreite()`
# direkt. Nach dem Tausch waere es ein Skript, das eine ANDERE Lage misst als
# die Produktion - genau die Umgehung, die ein glatter Schnitt ausschliessen
# soll. Es geht jetzt ueber `rollen_eingabe.baue_lagebild_eingabe()`, die
# einzige Stelle, an der die Eingabe des Lagebilds entsteht.
#
# WICHTIG FUER ALTE ERGEBNISSE: alles, was vor dem 12.08. mit diesem Skript
# gemessen wurde, traegt die Marktbreite. Ein Vergleich alt/neu ueber diese
# Grenze hinweg misst den Umbau mit, nicht die Sache.
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

import numpy as np


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--anker", default="ankerpopulation.json")
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="faktorzahl.json")
    p.add_argument("--trocken", action="store_true")
    args = p.parse_args()

    # EINE Datenquelle - siehe Modulkopf. Muss VOR dem ersten Zugriff stehen.
    import pruefe_rollenkette as PR
    PR.DB = args.db

    import agent.rolle_analyst as RA
    import agent.rolle_trader as RT
    from agent.lagebeschreibung import beschreibe_lage
    from backtest_llm1_historisch import lade_reihen_aus_db
    from indicators.calculations import atr_wilder, latest_value

    anker = json.load(open(args.anker, encoding="utf-8"))["anker"]
    reihen = lade_reihen_aus_db(args.db)
    print(f"DATENSTAND: {args.db}")
    print(f"PROMPT_STAND: {RA.PROMPT_STAND}")
    print(f"{len(anker)} Anker aus {args.anker}\n")

    # --- Vorflug: loesen alle Anker auf, bevor ein Aufruf faellt? ----------
    gueltig = []
    for a in anker:
        r = reihen.get(a["symbol"])
        if not r or a["index"] >= len(r):
            print(f"  {a['symbol']} {a['datum']}: Reihe fehlt oder zu kurz")
            continue
        if r[a["index"]].date[:10] != a["datum"][:10]:
            print(f"  {a['symbol']} {a['datum']}: Index zeigt auf "
                  f"{r[a['index']].date} - ANDERER DATENSTAND")
            continue
        gueltig.append(a)
    print(f"Vorflug: {len(gueltig)} von {len(anker)} Ankern loesen sauber auf")
    print(f"KONTINGENT: {len(gueltig)} x 2 Rollen = {len(gueltig)*2} Aufrufe")
    print("  Gemini: 10/min, 500/Tag je Modell -> Dauer rund "
          f"{len(gueltig)*2/10:.0f} Minuten\n")
    if args.trocken:
        print("TROCKEN - keine Aufrufe. Ohne --trocken laeuft die Messung.")
        return 0

    client, modell = PR._client(args.anbieter)
    ergebnisse = []
    for a in gueltig:
        sym, i = a["symbol"], a["index"]
        r = reihen[sym]
        zeile = dict(a)
        try:
            lage_ein = RE.baue_lagebild_eingabe(reihen, a["datum"])
            lage = RA.validiere(PR.frage(client, modell,
                                         RA.SYSTEM_PROMPT_ANALYST, lage_ein,
                                         "agent.rolle_analyst"))
            menge, einstand = PR._bestand(sym)
            hh = np.array([k.high for k in r[:i + 1]], dtype=float)
            ll = np.array([k.low for k in r[:i + 1]], dtype=float)
            cc = np.array([k.close for k in r[:i + 1]], dtype=float)
            atr = float(latest_value(atr_wilder(hh, ll, cc)) or 0.0)
            stand = beschreibe_lage(symbol=sym, reihe=r, index=i,
                                    kurs_eur=PR._kurs_eur(sym, r, i) or 0.0,
                                    atr=atr, menge=menge, einstand_eur=einstand)
            ein = {"asset": sym, "stand": stand,
                   "marktlage_beurteilung": {"lage": lage["lage"], "gleichlauf": lage.get("gleichlauf")}}
            roh = PR.frage(client, modell, RT.SYSTEM_PROMPT_TRADER, ein,
                           "agent.rolle_trader")
            ent = RT.validiere(dict(roh), sym)
            zeile.update({
                "faktoren": ent.get("unabhaengige_faktoren"),
                "aktion": ent.get("aktion"),
                "belege": len(ent.get("belege") or []),
                "begruendung": ent.get("begruendung"),
                "umgeworfen_durch": ent.get("umgeworfen_durch"),
                "bestand_vorhanden": bool(menge and einstand),
            })
        except Exception as e:                                   # noqa: BLE001
            zeile["fehler"] = f"{type(e).__name__}: {str(e)[:90]}"
        f = zeile.get("faktoren")
        print(f"  {sym:6} {a['datum']}  Zelle {a['zelle']}  "
              f"Faktoren={str(f):4} -> {zeile.get('aktion') or zeile.get('fehler','?')}")
        ergebnisse.append(zeile)
        with open(args.ausgabe, "w", encoding="utf-8") as fh:
            json.dump(ergebnisse, fh, ensure_ascii=False, indent=1)

    # --- Auswertung -------------------------------------------------------
    ok = [z for z in ergebnisse if "fehler" not in z and z.get("faktoren") is not None]
    print("\n" + "=" * 62)
    print("HANDLUNGSQUOTE JE FAKTORZAHL")
    print(f"{'Faktoren':>9} {'Faelle':>7} {'Handlungen':>11} {'Quote':>8}   Aktionen")
    print("-" * 62)
    je = defaultdict(list)
    for z in ok:
        je[z["faktoren"]].append(z)
    for f in sorted(je):
        gruppe = je[f]
        h = [z for z in gruppe if z["aktion"] != "NICHTS_TUN"]
        c = Counter(z["aktion"] for z in gruppe)
        print(f"{f:9} {len(gruppe):7} {len(h):11} {100*len(h)/len(gruppe):7.0f} %   "
              f"{dict(c)}")
    print("\nLESART: Steigt die Quote mit der Faktorzahl, wendet das System den")
    print("Fachstandard an (3-4 unabhaengige Faktoren tragen ein Setup, 1-2")
    print("nicht) - dann ist der Deadloop keine Fehlfunktion, sondern die")
    print("richtige Antwort auf eine zu duenne Eingabe.")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
