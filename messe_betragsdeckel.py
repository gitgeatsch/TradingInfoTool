# -*- coding: utf-8 -*-
"""Wirkt ein vorgegebener Hoechstbetrag als Handlungsaufforderung? - gepaart.

DIE HYPOTHESE stammt aus einem EINZELFALL vom 10.08.: am selben Anker (BTC,
22.07.2025) sagte das Modell mit einem Deckel von Rolle A "NACHKAUFEN 500 EUR",
ohne Deckel "NICHTS_TUN". Vermutung: *"hoechstens 500 EUR"* liest sich als
Erlaubnis, 500 einzusetzen - passend zum externen Befund, dass Modelle
Anweisungen auch dann folgen, wenn es zu Verlusten fuehrt.

**Ein Fall ist kein Beleg.** Diese Messung macht daraus eine Zahl.

DER AUFBAU - streng gepaart:

    Arm MIT     Rolle A nennt einen Hoechstbetrag, Rolle BC bekommt ihn
    Arm OHNE    Rolle A nennt keinen (der heutige Produktivstand)

Beide Arme bekommen BITGLEICH DIESELBEN FAKTEN, denselben Anker, denselben
Anbieter. Der einzige Unterschied ist der Deckel. Alles andere gepaart zu
halten ist der ganze Punkt - sonst misst man den Anker statt den Deckel.

ZWEI MASSE, und sie koennen sich widersprechen:

    HANDLUNGSQUOTE   wie oft wird ueberhaupt gehandelt? Das Ziel ist MEHR
                     Signale - ein Arm, der nie handelt, ist nutzlos.
    TREFFERQUOTE     wie oft war die Handlung richtig, gemessen an der
                     tatsaechlichen Kursbewegung 20 Tage danach?

Ein Deckel, der die Handlungsquote hebt UND die Trefferquote senkt, ist eine
Handlungsaufforderung. Einer, der beides hebt, waere ein Gewinn.

DIE ANKER decken bewusst mehrere Assetklassen und Richtungen ab (Nutzervorgabe
11.08.: *"die Pruefung bei Altcoins ist schwierig, sollte bei anderen Assets
besser funktionieren - teste auch BTC und ggf. Aktien"*). Bei Aktien gibt es
die Aufwaertsphasen, die im Krypto-Zeitraum fehlen - VST +48,3 %, PLTR +22,3 %.

    python messe_betragsdeckel.py --anbieter gemini35
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
import sqlite3
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

# Symbol, Datum - gemischt ueber Assetklassen, Richtungen und Ausgaenge.
# Die Vorwaertsrendite steht NICHT hier: sie wird aus der Kursreihe gelesen,
# damit sie nicht versehentlich zur Auswahl beigetragen hat.
ANKER = (
    ("VST",  "2024-09-16"), ("VST",  "2022-12-16"), ("VST",  "2019-07-01"),
    ("PLTR", "2024-07-24"), ("PLTR", "2022-09-06"), ("PLTR", "2026-06-11"),
)

# Der Deckel-Prompt fuer Arm MIT. Rekonstruiert aus der Fassung vom 10.08.,
# BEVOR der Betrag entfernt wurde - damit die Messung den echten Unterschied
# abbildet und nicht eine nachtraeglich erfundene Variante.
DECKEL_ZUSATZ = """

HOECHSTBETRAG: Welcher Einzelbetrag ist in dieser Lage angemessen - 100, 300 \
oder 500 Euro? Das ist eine Obergrenze fuer eine einzelne Position.
Gib ihn als zusaetzliches Feld "max_tranche_eur" aus."""


def _atr(reihe, i: int) -> float:
    h = np.array([k.high for k in reihe[:i + 1]], dtype=float)
    l = np.array([k.low for k in reihe[:i + 1]], dtype=float)
    c = np.array([k.close for k in reihe[:i + 1]], dtype=float)
    return float(latest_value(atr_wilder(h, l, c)) or 0.0)


def wahrheit(reihe, idx: int, horizont: int = 20) -> float | None:
    """Was tatsaechlich geschah - aus der Kursreihe, nicht aus einer Schaetzung."""
    j = idx + horizont
    if j >= len(reihe):
        return None
    return 100.0 * (reihe[j].close / reihe[idx].close - 1.0)


def war_richtig(aktion: str, rendite: float) -> bool | None:
    """War die Handlung richtig, gemessen am tatsaechlichen Verlauf?

    NICHTS_TUN zaehlt nicht mit - es ist weder richtig noch falsch, sondern
    die Abwesenheit einer Entscheidung. Wer es mitzaehlte, koennte die
    Trefferquote durch Nichtstun beliebig hochtreiben."""
    if aktion in ("KAUFEN", "NACHKAUFEN"):
        return rendite > 0
    if aktion in ("REDUZIEREN", "VERKAUFEN"):
        return rendite < 0
    return None


def lauf_arm(client, modell, symbol, reihe, idx, reihen, mit_deckel: bool):
    anker = reihe[idx].date
    a_ein = RE.baue_lagebild_eingabe(reihen, anker)
    menge, einstand = _bestand(symbol)
    bc_ein = {"asset": symbol,
              "stand": beschreibe_lage(symbol=symbol, reihe=reihe, index=idx,
                                       kurs_eur=_kurs_eur(symbol, reihe, idx) or 0.0,
                                       atr=_atr(reihe, idx), menge=menge,
                                       einstand_eur=einstand)}
    prompt_a = RA.SYSTEM_PROMPT_ANALYST + (DECKEL_ZUSATZ if mit_deckel else "")
    a_roh = frage(client, modell, prompt_a, a_ein, "agent.rolle_analyst")
    deckel = None
    if mit_deckel:
        try:
            deckel = int(float(a_roh.get("max_tranche_eur")))
        except (TypeError, ValueError):
            deckel = None
        a_roh.pop("max_tranche_eur", None)
    a = RA.validiere(a_roh)

    bc_ein["marktlage_beurteilung"] = {"lage": a["lage"], "gleichlauf": a.get("gleichlauf")}
    if deckel:
        bc_ein["marktlage_beurteilung"]["hoechstbetrag_eur"] = deckel
    bc_roh = frage(client, modell, RT.SYSTEM_PROMPT_TRADER, bc_ein,
                   "agent.rolle_trader")
    return RT.validiere(bc_roh, symbol), deckel


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="betragsdeckel.json")
    args = p.parse_args()

    print(f"KONTINGENT: {len(ANKER)} Anker x 2 Arme x 2 Rollen = "
          f"{len(ANKER)*4} Aufrufe an {args.anbieter}")
    reihen = lade_reihen_aus_db()
    client, modell = _client(args.anbieter)
    ergebnisse = []

    for symbol, datum in ANKER:
        reihe = reihen.get(symbol)
        if not reihe:
            print(f"  {symbol} fehlt"); continue
        idx = next((i for i, k in enumerate(reihe) if k.date >= datum), None)
        if idx is None or idx < 220:
            print(f"  {symbol} {datum}: zu frueh"); continue
        w = wahrheit(reihe, idx)
        if w is None:
            print(f"  {symbol} {datum}: keine 20 Tage Zukunft"); continue

        zeile = {"symbol": symbol, "datum": datum, "rendite_20t": round(w, 1)}
        for mit in (True, False):
            arm = "mit" if mit else "ohne"
            try:
                bc, deckel = lauf_arm(client, modell, symbol, reihe, idx, reihen, mit)
                zeile[arm] = {"aktion": bc["aktion"],
                              "betrag": bc.get("tranche_eur"),
                              "deckel": deckel,
                              "faktoren": bc.get("unabhaengige_faktoren"),
                              "richtig": war_richtig(bc["aktion"], w)}
            except (EmpfehlungUngueltig, RT.TraderAntwortUngueltig,
                    RA.AnalystAntwortUngueltig) as e:
                zeile[arm] = {"fehler": str(e)[:90]}
            except Exception as e:
                zeile[arm] = {"fehler": f"{type(e).__name__}: {str(e)[:70]}"}
        m, o = zeile.get("mit", {}), zeile.get("ohne", {})
        print(f"  {symbol:5} {datum}  danach {w:+6.1f} %   "
              f"MIT: {m.get('aktion') or m.get('fehler','?'):11} "
              f"OHNE: {o.get('aktion') or o.get('fehler','?'):11}")
        ergebnisse.append(zeile)
        with open(args.ausgabe, "w", encoding="utf-8") as f:
            json.dump(ergebnisse, f, ensure_ascii=False, indent=1)

    # --- Auswertung ---------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"{'Arm':6} {'Handlungen':>12} {'davon richtig':>15} {'Trefferquote':>14}")
    print("-" * 70)
    for arm in ("mit", "ohne"):
        gueltig = [z[arm] for z in ergebnisse if arm in z and "fehler" not in z[arm]]
        handlungen = [x for x in gueltig if x["richtig"] is not None]
        richtig = [x for x in handlungen if x["richtig"]]
        quote = f"{100.0*len(richtig)/len(handlungen):.0f} %" if handlungen else "-"
        print(f"{arm:6} {len(handlungen):5} von {len(gueltig):<4} "
              f"{len(richtig):15} {quote:>14}")
    print("\nLESART: ein Deckel, der die Handlungszahl HEBT und die Trefferquote")
    print("SENKT, wirkt als Handlungsaufforderung. Hebt er beides, ist er ein")
    print("Gewinn. Aendert sich nichts, war die Einzelfall-Beobachtung Zufall.")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
