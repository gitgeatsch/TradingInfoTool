# -*- coding: utf-8 -*-
"""Wie muss die AUSWAHL dimensioniert sein? (23.08.2026)

⚠️ DIE NUTZERFRAGE, DIE DIESES WERKZEUG AUSGELOEST HAT:

    "Was meinst du konkret mit 'Auswahl'? Hier versteckst du gerne Fakten,
     die erst spaeter in der Diskussion genannt werden."

BERECHTIGT. "Auswahl" ist ein Sammelwort. Was darin steckt und hier gemessen
wird:

    WIEVIELE     k - die Zahl, die ich nie genannt habe
    WORAUS       je Gruppe oder ueber alle
    UND WENN ALLE SCHLECHT SIND? - eine Rangliste hat IMMER einen Sieger.
                 Eine reine Auswahl unterstellt also lautlos: es wird
                 gekauft. Das ist die versteckteste Annahme von allen.

DIE LITERATUR KENNT GENAU DIESE LUECKE UND IHRE LOESUNG:

    "Antonacci (2014) formalisierte die Verbindung von relativer Auswahl mit
     einem absoluten Trendfilter zum DUAL MOMENTUM ... Assets werden nach
     relativer Staerke ausgewaehlt und nur aufgenommen, wenn sie ABSOLUT
     positives Momentum aufweisen."
     - Risk Premia Harvesting Through Dual Momentum, Gary Antonacci
       https://www.optimalmomentum.com/dual-relative-absolute-momentum/
     - Dual vs. Single Momentum in Commodities, QuantPedia
       https://quantpedia.com/dual-vs-single-momentum-in-commodities-enhancing-risk-adjusted-returns-through-absolute-trend-filtering/

    RELATIV entscheidet WELCHEN. ABSOLUT entscheidet OB.

Beides ist im Projekt vorhanden, aber nur die erste Haelfte war je gemessen.

GEMESSEN WIRD DESHALB:

    1. k-Empfindlichkeit   traegt "die besten 3" mehr als "das beste Fuenftel"?
    2. absolut oder nicht  was passiert ohne den Trendfilter - und mit ihm?
    3. Sperrquote          wie oft sperrt der Filter ALLES? (Das ist der
                           Preis: Umlaeufe ohne Signal)
    4. je Marktzustand     getrennt nach BTC ueber/unter seinem 200-Schnitt
    5. Gruppengroesse      "die besten 2 von 2" ist keine Auswahl

MASS: Vorwaertsrendite ueber einen festen Horizont, barrierenfrei und BRUTTO
(Potential, Nutzervorgabe 23.08.). Signifikanz ueber Termine mit Newey-West,
weil sich an einem Tag alles gemeinsam bewegt.

⚠️ ZWEI ZAHLEN, NICHT EINE. Der ABSTAND zum Markt sagt, ob die Auswahl trennt.
Die ABSOLUTE Rendite sagt, ob sich der Kauf ueberhaupt lohnt. Nur die erste zu
zeigen, waere genau das Verstecken, das der Nutzer benannt hat.
"""
from __future__ import annotations

import argparse

import numpy as np

from messe_drift import _newey_west, _reihen, _tafel

RUECKBLICK = 250          # das einzige Feld, das die Placebo-Schwelle hielt
HORIZONTE = (5, 20)
K_WERTE = (1, 2, 3, 5, 8)
MIND_SYMBOLE = 10
SMA_MARKT = 200


def marktzustand(tafel, symbole, t: int) -> float | None:
    """BTCs Abstand zu seinem eigenen 200-Tage-Schnitt - stetig, kein Etikett."""
    if "BTC" not in symbole:
        return None
    i = symbole.index("BTC")
    fenster = tafel[i, max(0, t - SMA_MARKT + 1):t + 1]
    fenster = fenster[~np.isnan(fenster)]
    if len(fenster) < SMA_MARKT // 2 or np.isnan(tafel[i, t]):
        return None
    return float(tafel[i, t] / fenster.mean() - 1.0)


def lauf(tafel, symbole, horizont: int, k: int, absolut: bool,
         termine=None):
    """Gibt je Termin (Rendite der Auswahl, Marktrendite, Zahl gewaehlt)."""
    n, T = tafel.shape
    aus = []
    for t in range(RUECKBLICK, T - horizont):
        gut = (~np.isnan(tafel[:, t]) & ~np.isnan(tafel[:, t - RUECKBLICK])
               & ~np.isnan(tafel[:, t + horizont]))
        if gut.sum() < MIND_SYMBOLE:
            continue
        rueck = tafel[:, t][gut] / tafel[:, t - RUECKBLICK][gut] - 1.0
        vor = tafel[:, t + horizont][gut] / tafel[:, t][gut] - 1.0
        if not (np.all(np.isfinite(rueck)) and np.all(np.isfinite(vor))):
            continue
        ordnung = np.argsort(-rueck)                 # bester zuerst
        gewaehlt = list(ordnung[:k])
        if absolut:
            # DUAL MOMENTUM: nur wer auch fuer sich genommen gestiegen ist.
            gewaehlt = [i for i in gewaehlt if rueck[i] > 0]
        aus.append((float(np.mean(vor[gewaehlt])) if gewaehlt else None,
                    float(np.mean(vor)), len(gewaehlt),
                    marktzustand(tafel, symbole, t),
                    str(termine[t])[:4] if termine is not None
                    else None))
    return aus


def zusammen(zeilen, nur_zustand=None) -> dict:
    z = [r for r in zeilen
         if nur_zustand is None
         or (r[3] is not None and nur_zustand(r[3]))]
    if not z:
        return {}
    mit = [r for r in z if r[0] is not None]
    leer = len(z) - len(mit)
    if len(mit) < 30:
        return {"termine": len(z), "leer": leer, "zu_duenn": True}
    auswahl = np.array([r[0] for r in mit])
    markt = np.array([r[1] for r in mit])
    abstand = auswahl - markt
    se_a = _newey_west(abstand, max(1, len(abstand) // 400))
    return {"termine": len(z), "leer": leer,
            "gewaehlt": float(np.mean([r[2] for r in mit])),
            "auswahl": float(auswahl.mean()), "markt": float(markt.mean()),
            "abstand": float(abstand.mean()),
            "t": float(abstand.mean() / se_a) if se_a > 0 else float("nan")}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    args = p.parse_args()

    reihen = _reihen(args.db, args.klasse)
    termine, tafel, symbole = _tafel(reihen)
    print(f"{args.klasse}: {len(symbole)} Symbole · {len(termine)} Tage "
          f"({termine[0]} bis {termine[-1]}) · Rueckblick {RUECKBLICK} Tage")
    print("Mass: Vorwaertsrendite, barrierenfrei und BRUTTO. "
          "Handelskosten ~3 % je Runde - sie fallen bei JEDER Wahl an.\n")

    for horizont in HORIZONTE:
        print(f"=== Horizont {horizont} Handelstage ===")
        print(f"{'k':>3} {'Filter':>8} {'Termine':>8} {'ohne':>6} "
              f"{'Auswahl':>9} {'Markt':>9} {'Abstand':>9} {'t':>7}")
        for k in K_WERTE:
            for absolut in (False, True):
                e = zusammen(lauf(tafel, symbole, horizont, k, absolut, termine))
                if not e or e.get("zu_duenn"):
                    continue
                print(f"{k:3} {'absolut' if absolut else 'nur Rang':>8} "
                      f"{e['termine']:8} {e['leer']:6} "
                      f"{100*e['auswahl']:8.2f}% {100*e['markt']:8.2f}% "
                      f"{100*e['abstand']:8.2f}% {e['t']:7.2f}")
        print()

    # --- Je Marktzustand, fuer k = 3 -------------------------------------
    print("=== k = 3, Horizont 5, getrennt nach Marktzustand (BTC zum "
          "200-Schnitt) ===")
    print(f"{'Zustand':22} {'Filter':>8} {'Termine':>8} {'ohne':>6} "
          f"{'Auswahl':>9} {'Markt':>9} {'Abstand':>9} {'t':>7}")
    zustaende = (("BTC ueber dem Schnitt", lambda x: x > 0),
                 ("BTC unter dem Schnitt", lambda x: x <= 0))
    for name, pruef in zustaende:
        for absolut in (False, True):
            e = zusammen(lauf(tafel, symbole, 5, 3, absolut, termine), pruef)
            if not e or e.get("zu_duenn"):
                print(f"{name:22} {'absolut' if absolut else 'nur Rang':>8} "
                      f"{'zu wenige Termine':>30}")
                continue
            print(f"{name:22} {'absolut' if absolut else 'nur Rang':>8} "
                  f"{e['termine']:8} {e['leer']:6} "
                  f"{100*e['auswahl']:8.2f}% {100*e['markt']:8.2f}% "
                  f"{100*e['abstand']:8.2f}% {e['t']:7.2f}")

    # --- DIE VORAB BENANNTE PRUEFUNG (Nutzerauftrag 23.08.) --------------
    #
    # ⚠️ EINE Frage, VORHER aufgeschrieben, damit sie nicht eine Zelle
    # unter vielen ist: traegt k=2 / Horizont 20 mit dem Marktzustand als
    # Schranke auch in JEDEM EINZELNEN JAHR - oder nur im Mittel ueber neun?
    print("")
    print("=== VORAB BENANNTE PRUEFUNG: k=2, Horizont 20, nur wenn BTC "
          "ueber seinem 200-Schnitt ===")
    print(f"{'Jahr':6} {'Termine':>8} {'Auswahl':>9} "
          f"{'Markt':>9} {'Abstand':>9} {'traegt?':>9}")
    zeilen = [r for r in lauf(tafel, symbole, 20, 2, False, termine)
              if r[3] is not None and r[3] > 0 and r[0] is not None]
    jahre = sorted({r[4] for r in zeilen})
    getragen = zaehlbar = 0
    for j in jahre:
        z = [r for r in zeilen if r[4] == j]
        if len(z) < 20:
            print(f"{j:6} {len(z):8}   zu wenige Termine")
            continue
        a = float(np.mean([r[0] for r in z]))
        m = float(np.mean([r[1] for r in z]))
        zaehlbar += 1
        getragen += 1 if a - m > 0 else 0
        print(f"{j:6} {len(z):8} {100*a:8.2f}% {100*m:8.2f}% "
              f"{100*(a-m):8.2f}% {"ja" if a - m > 0 else "NEIN":>9}")
    print("")
    print(f"   {getragen} von {zaehlbar} auswertbaren Jahren mit positivem "
          f"Abstand.")

    print("\n⚠️ 'ohne' = Termine, an denen der absolute Filter ALLES sperrt. "
          "Das ist der Preis\n   der Auswahl: Umlaeufe ohne Signal. Eine "
          "Rangliste allein hat immer einen Sieger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
