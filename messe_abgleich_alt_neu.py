# -*- coding: utf-8 -*-
"""Hebt der Umbau den Deadloop auf? Alt gegen neu, auf DENSELBEN Faellen.

DER FEHLER, DEN DAS BEHEBT (Nutzereinwand 12.08.). Am 11.08. wurden zwei Dinge
vermischt:

    97,7 % HALTEN     gemessen am ALTEN Produktivsystem (2.957 Signale)
    34-40 % Handlung  gemessen an der NEUEN Rollen-Ebene (geschichtete Anker)

Und dazwischen wurde den ganzen Tag nach URSACHEN fuer das Verhalten des
Altsystems gesucht, indem an der NEUEN Kette manipuliert wurde - Struktur-
Etikett, Degradierung, Faktorzahl, alles auf Prompt-Stand 2026-08-11. Jede
Erklaerung lief ins Leere, und das war zu erwarten: gesucht wurde die Ursache
eines Phaenomens, das das getestete System gar nicht zeigt.

DAS ZIEL DES UMBAUS ist erklaert: das System muss funktionieren, der Deadloop
muss weg. Ob er weg ist, laesst sich nur an DENSELBEN Faellen entscheiden - eine
Handlungsquote auf geschichteten Ankern gegen eine auf Produktionskandidaten zu
halten, vergleicht zwei Grundgesamtheiten und nicht zwei Systeme.

DER AUFBAU

    Stichprobe aus den echten Signalen (Symbol + Tag + die damalige Aktion),
    zufaellig gezogen mit festem Seed, OHNE Schichtung nach Aktion - damit die
    Mischung der Produktion erhalten bleibt.

    Auf jedem dieser Faelle laeuft die neue Kette. Verglichen werden die
    Handlungsquoten, nicht die Richtigkeit: ob eine Handlung gut war, ist eine
    andere Frage und nach Arbeitsstand 7.25 ohnehin anders zu stellen.

EIN LAGEBILD JE TAG. Es haengt nicht vom Asset ab; mehrere Signale desselben
Tages teilen es sich. Das spart Aufrufe und macht die Faelle eines Tages
untereinander vergleichbar.

    python messe_abgleich_alt_neu.py --db <pfad> --n 50 --trocken
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
import random
import sqlite3
import sys
from collections import Counter

import numpy as np

SEED = 20260812


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="abgleich_alt_neu.json")
    p.add_argument("--trocken", action="store_true")
    args = p.parse_args()

    import pruefe_rollenkette as PR
    PR.DB = args.db

    import agent.rolle_analyst as RA
    import agent.rolle_trader as RT
    from agent.lagebeschreibung import beschreibe_lage
    from backtest_llm1_historisch import lade_reihen_aus_db
    from indicators.calculations import atr_wilder, latest_value

    c = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    roh = c.execute("select symbol, date(created_at), action from signals").fetchall()
    reihen = lade_reihen_aus_db(args.db)

    faelle = []
    for sym, tag, aktion in roh:
        r = reihen.get(sym)
        if not r:
            continue
        idx = next((i for i, k in enumerate(r) if k.date >= tag), None)
        if idx is None or idx < 220:
            continue
        faelle.append({"symbol": sym, "datum": tag, "alt": aktion, "index": idx})

    quote_alt_gesamt = (sum(1 for f in faelle if f["alt"] != "HALTEN")
                        / len(faelle) if faelle else 0)
    rng = random.Random(SEED)
    stichprobe = rng.sample(faelle, min(args.n, len(faelle)))
    tage = sorted({f["datum"] for f in stichprobe})

    print(f"DATENSTAND: {args.db}   PROMPT_STAND: {RA.PROMPT_STAND}")
    print(f"{len(faelle)} auswertbare Produktionsfaelle, "
          f"Handlungsquote ALT {100*quote_alt_gesamt:.1f} %")
    print(f"Stichprobe: {len(stichprobe)} Faelle ueber {len(tage)} Tage")
    print(f"  darin ALT: {dict(Counter(f['alt'] for f in stichprobe))}")
    print(f"KONTINGENT: {len(tage)} Lagebilder + {len(stichprobe)} Entscheidungen "
          f"= {len(tage)+len(stichprobe)} Aufrufe")
    print(f"  Gemini 10/min, 500/Tag -> rund "
          f"{(len(tage)+len(stichprobe))/10:.0f} Minuten\n")
    if args.trocken:
        print("TROCKEN - keine Aufrufe.")
        return 0

    client, modell = PR._client(args.anbieter)
    lagebilder: dict = {}
    ergebnisse = []
    for f in stichprobe:
        sym, i, tag = f["symbol"], f["index"], f["datum"]
        r = reihen[sym]
        try:
            if tag not in lagebilder:
                lagebilder[tag] = RA.validiere(PR.frage(
                    client, modell, RA.SYSTEM_PROMPT_ANALYST,
                    RE.baue_lagebild_eingabe(reihen, tag),
                    "agent.rolle_analyst"))
            lage = lagebilder[tag]
            menge, einstand = PR._bestand(sym)
            hh = np.array([k.high for k in r[:i + 1]], dtype=float)
            ll = np.array([k.low for k in r[:i + 1]], dtype=float)
            cc = np.array([k.close for k in r[:i + 1]], dtype=float)
            atr = float(latest_value(atr_wilder(hh, ll, cc)) or 0.0)
            ein = {"asset": sym,
                   "stand": beschreibe_lage(symbol=sym, reihe=r, index=i,
                                            kurs_eur=PR._kurs_eur(sym, r, i) or 0.0,
                                            atr=atr, menge=menge,
                                            einstand_eur=einstand),
                   "marktlage_beurteilung": {"lage": lage["lage"], "gleichlauf": lage.get("gleichlauf")}}
            ent = RT.validiere(dict(PR.frage(client, modell,
                                             RT.SYSTEM_PROMPT_TRADER, ein,
                                             "agent.rolle_trader")), sym, atr=atr)
            f["neu"] = ent.get("aktion")
            f["faktoren"] = ent.get("unabhaengige_faktoren")
            f["begruendung"] = ent.get("begruendung")
        except Exception as e:                                   # noqa: BLE001
            f["fehler"] = f"{type(e).__name__}: {str(e)[:90]}"
        print(f"  {sym:9} {tag}  ALT {f['alt']:11} -> NEU "
              f"{str(f.get('neu') or f.get('fehler','?')):12}")
        ergebnisse.append(f)
        with open(args.ausgabe, "w", encoding="utf-8") as fh:
            json.dump(ergebnisse, fh, ensure_ascii=False, indent=1)

    ok = [z for z in ergebnisse if "fehler" not in z]
    h_alt = [z for z in ok if z["alt"] != "HALTEN"]
    h_neu = [z for z in ok if z["neu"] not in (None, "NICHTS_TUN")]
    print("\n" + "=" * 60)
    print(f"AUF DENSELBEN {len(ok)} FAELLEN")
    print(f"  ALT  {len(h_alt):3} Handlungen = {100*len(h_alt)/len(ok):5.1f} %"
          f"   {dict(Counter(z['alt'] for z in ok))}")
    print(f"  NEU  {len(h_neu):3} Handlungen = {100*len(h_neu)/len(ok):5.1f} %"
          f"   {dict(Counter(z['neu'] for z in ok))}")
    print("\nLESART: Das erklaerte Ziel des Umbaus war, den Deadloop aufzuheben.")
    print("Erst dieser Vergleich - dieselben Faelle, beide Systeme - kann sagen,")
    print("ob er erreicht ist. Eine Quote auf anderen Ankern kann es nicht.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
