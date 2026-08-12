# -*- coding: utf-8 -*-
"""Sind die NICHTS_TUN der acht Anker Urteile - oder degradierte Kaeufe?

DIE FRAGE (11.08. abends). `empfehlung_vertrag.validiere()` nimmt eine
Kaufempfehlung ohne gueltigen Ausstieg auf NICHTS_TUN zurueck (R-A7):

    if einstieg is None or stop is None:  grund = "ohne Einstieg oder Ausstieg"
    elif stop >= einstieg:                grund = "Ausstieg liegt nicht unter dem Einstieg"
    if grund: antwort["aktion"] = "NICHTS_TUN"

Das ist richtig gebaut - ein Kauf ohne Ausstieg IST gefaehrlich. Aber alle
bisherigen Messskripte haben nur `aktion` gespeichert. Damit ist ein
degradierter Kauf von einem abgewogenen NICHTS_TUN nicht unterscheidbar, und
der Befund aus Arbeitsstand 7.8 ("das System kauft fast nie") kann beides
bedeuten. Dieses Skript trennt sie.

WAS GEGENUEBER `messe_betragsdeckel.py` BEHOBEN IST (Arbeitsstand 7.10):

  K1  Erfolgsmass mit STOP statt 20-Tage-Endrendite. Ein Trade mit +22,3 %
      Endrendite kann ausgestoppt worden sein - PLTR 2024-07-24 war es
      (zwischenzeitlich -10,7 %). Hier laeuft ein Erstdurchgang: was kommt
      zuerst, Ziel oder Stop? Und die Zeitschranke wird NICHT gewaehlt,
      sondern als Kurve ueber 5/10/20/40 Tage berichtet.
  K2  Es wird ALLES gespeichert, was die Deutung traegt: Begruendung, Belege,
      `_degradiert`, `_korrekturen`, ob ein Bestand vorlag, und der
      Prompt-Stand. Ein Befund ohne Prompt-Stand ist nicht zuordenbar.
  K3  Die Ankerliste ist versioniert und benannt, statt zwischen Laeufen
      ueberschrieben zu werden.

KEIN VERGLEICHSARM. Dieser Lauf ist diagnostisch, nicht gepaart - er fragt
NUR, was hinter den NICHTS_TUN steckt. Die gepaarte Messung zur Betragsfrage
ist ein eigener Lauf mit eigenem Aufbau.

    python messe_degradierung.py --anbieter gemini35
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
from collections import Counter

import numpy as np

import agent.rolle_analyst as RA
import agent.rolle_trader as RT
from agent.empfehlung_vertrag import EmpfehlungUngueltig
import agent.rollen_eingabe as RE
from agent.lagebeschreibung import beschreibe_lage
from backtest_llm1_historisch import lade_reihen_aus_db
from indicators.calculations import atr_wilder, latest_value
from pruefe_rollenkette import _bestand, _client, _kurs_eur, frage

# K3 - benannt und versioniert. Diese acht sind die Anker aus Arbeitsstand
# 7.8/7.9, deren Ausgang dort dokumentiert ist. Sie sind NACH IHREM AUSGANG
# ausgewaehlt (grosse Gewinne) und taugen deshalb NICHT fuer eine Trefferquote -
# nur fuer die Frage, was hinter einem NICHTS_TUN steckt.
ANKER_7_8 = (
    ("BTC",  "2025-06-24"), ("BTC",  "2025-12-25"), ("BTC",  "2026-03-27"),
    ("ETH",  "2025-06-24"), ("ETH",  "2026-03-27"),
    ("VST",  "2024-09-16"),
    ("PLTR", "2022-09-06"), ("PLTR", "2024-07-24"),
)

ZIEL_ATR = 3.0
STOP_ATR = 1.5
HORIZONTE = (5, 10, 20, 40)


def _atr(reihe, i: int) -> float:
    h = np.array([k.high for k in reihe[:i + 1]], dtype=float)
    l = np.array([k.low for k in reihe[:i + 1]], dtype=float)
    c = np.array([k.close for k in reihe[:i + 1]], dtype=float)
    return float(latest_value(atr_wilder(h, l, c)) or 0.0)


def erstdurchgang(reihe, idx: int, atr: float) -> dict:
    """K1 - was zuerst erreicht wird, Ziel oder Stop, je Zeitschranke.

    Einstieg zum Schlusskurs des Ankertags. Beruehren High und Low am selben
    Tag beide Schwellen, wird der STOP gewertet: aus Tagesdaten ist die
    Reihenfolge innerhalb des Tages nicht erkennbar, und die guenstige Annahme
    waere genau die, die eine Strategie im Rueckblick zu gut aussehen laesst."""
    if atr <= 0:
        return {"fehler": "ATR nicht berechenbar"}
    einstieg = float(reihe[idx].close)
    ziel, stop = einstieg + ZIEL_ATR * atr, einstieg - STOP_ATR * atr
    aus = {"einstieg": round(einstieg, 4),
           "ziel": round(ziel, 4), "stop": round(stop, 4)}
    ergebnis, tag = None, None
    for n in range(1, max(HORIZONTE) + 1):
        j = idx + n
        if j >= len(reihe):
            break
        if float(reihe[j].low) <= stop:
            ergebnis, tag = "STOP", n
            break
        if float(reihe[j].high) >= ziel:
            ergebnis, tag = "ZIEL", n
            break
    for h in HORIZONTE:
        if ergebnis and tag <= h:
            aus[f"bis_{h}t"] = ergebnis
        elif idx + h < len(reihe):
            aus[f"bis_{h}t"] = "offen"
        else:
            aus[f"bis_{h}t"] = "keine Daten"
    aus["ereignis"] = ergebnis or "keines"
    aus["ereignis_tag"] = tag
    return aus


def lauf(client, modell, symbol, reihe, idx, reihen) -> dict:
    """Ein Anker, beide Rollen, alles mitgeschrieben (K2)."""
    anker = reihe[idx].date
    menge, einstand = _bestand(symbol)

    lage_ein = RE.baue_lagebild_eingabe(reihen, anker)
    lage_roh = frage(client, modell, RA.SYSTEM_PROMPT_ANALYST, lage_ein,
                     "agent.rolle_analyst")
    lage = RA.validiere(lage_roh)

    stand = beschreibe_lage(symbol=symbol, reihe=reihe, index=idx,
                            kurs_eur=_kurs_eur(symbol, reihe, idx) or 0.0,
                            atr=_atr(reihe, idx), menge=menge,
                            einstand_eur=einstand)
    ent_ein = {"asset": symbol, "stand": stand,
               "marktlage_beurteilung": {"traegt": lage["traegt"],
                                         "lage": lage["lage"]}}
    ent_roh = frage(client, modell, RT.SYSTEM_PROMPT_TRADER, ent_ein,
                    "agent.rolle_trader")
    # Die ROHE Aktion vor dem Vertrag - nur so ist ein degradierter Kauf sichtbar.
    aktion_roh = str(ent_roh.get("aktion") or "?").upper()
    ent = RT.validiere(dict(ent_roh), symbol)

    return {
        "aktion_roh": aktion_roh,
        "aktion": ent.get("aktion"),
        "degradiert": ent.get("_degradiert"),
        "korrekturen": ent.get("_korrekturen"),
        "einstieg_eur_modell": ent_roh.get("einstieg_eur"),
        "stop_eur_modell": ent_roh.get("stop_eur"),
        "unabhaengige_faktoren": ent.get("unabhaengige_faktoren"),
        "begruendung": ent.get("begruendung"),
        "was_dagegen": ent.get("was_dagegen"),
        # NACHGETRAGEN 11.08.: fehlte im ersten Lauf - ausgerechnet das Feld,
        # das als Ausstiegskriterium dienen soll. K2 gilt auch fuer mich.
        "umgeworfen_durch": ent.get("umgeworfen_durch"),
        "belege": ent.get("belege"),
        "lage_text": lage.get("lage"),
        "lage_traegt": lage.get("traegt"),
        "stand_text": stand,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="degradierung.json")
    args = p.parse_args()

    print(f"KONTINGENT: {len(ANKER_7_8)} Anker x 2 Rollen = "
          f"{len(ANKER_7_8) * 2} Aufrufe an {args.anbieter}")
    print(f"PROMPT_STAND: {RA.PROMPT_STAND} / {RT.PROMPT_STAND}\n")

    reihen = lade_reihen_aus_db()
    client, modell = _client(args.anbieter)
    ergebnisse = []

    for symbol, datum in ANKER_7_8:
        reihe = reihen.get(symbol)
        if not reihe:
            print(f"  {symbol} fehlt"); continue
        idx = next((i for i, k in enumerate(reihe) if k.date >= datum), None)
        if idx is None or idx < 220:
            print(f"  {symbol} {datum}: zu frueh"); continue

        menge, einstand = _bestand(symbol)
        zeile = {
            "symbol": symbol, "datum": datum,
            "prompt_stand": RA.PROMPT_STAND,
            # Der Bestand ist eine NAEHERUNG (heutiger statt damaliger) - das
            # steht hier, damit es bei der Deutung nicht vergessen wird.
            "bestand_vorhanden": bool(menge and einstand),
            "ausgang": erstdurchgang(reihe, idx, _atr(reihe, idx)),
        }
        try:
            zeile.update(lauf(client, modell, symbol, reihe, idx, reihen))
        except (EmpfehlungUngueltig, RT.TraderAntwortUngueltig,
                RA.AnalystAntwortUngueltig) as e:
            zeile["fehler"] = str(e)[:120]
        except Exception as e:
            zeile["fehler"] = f"{type(e).__name__}: {str(e)[:100]}"

        d = " DEGRADIERT" if zeile.get("degradiert") else ""
        print(f"  {symbol:5} {datum}  Bestand={'ja' if zeile['bestand_vorhanden'] else 'nein':4} "
              f"roh={zeile.get('aktion_roh') or zeile.get('fehler','?'):12} "
              f"final={zeile.get('aktion','?'):11} "
              f"Ausgang={zeile['ausgang'].get('ereignis','?'):7}{d}")
        ergebnisse.append(zeile)
        with open(args.ausgabe, "w", encoding="utf-8") as f:
            json.dump(ergebnisse, f, ensure_ascii=False, indent=1)

    print("\n" + "=" * 72)
    gueltig = [z for z in ergebnisse if "fehler" not in z]
    roh = Counter(z["aktion_roh"] for z in gueltig)
    final = Counter(z["aktion"] for z in gueltig)
    degradiert = [z for z in gueltig if z.get("degradiert")]
    print(f"ROH (was das Modell sagte):    {dict(roh)}")
    print(f"FINAL (nach dem Vertrag):      {dict(final)}")
    print(f"\nDEGRADIERTE KAEUFE: {len(degradiert)} von {len(gueltig)}")
    for z in degradiert:
        print(f"   {z['symbol']:5} {z['datum']}  {z['degradiert']}")
    print("\nLESART: Sind die NICHTS_TUN roh schon NICHTS_TUN, war es ein")
    print("Urteil. Stehen dort KAUFEN/NACHKAUFEN, hat die Arithmetik sie")
    print("gekippt - ein mechanischer Deadloop-Pfad ohne jedes Urteil.")
    print("\nERSTDURCHGANG (K1, mit Stop gerechnet):")
    for h in HORIZONTE:
        c = Counter(z["ausgang"].get(f"bis_{h}t") for z in gueltig)
        print(f"   bis {h:2} Tage: {dict(c)}")
    print(f"\nGeschrieben: {args.ausgabe}  (Prompt-Stand {RA.PROMPT_STAND})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
