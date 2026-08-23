# -*- coding: utf-8 -*-
"""Was haette die Auswahl ueber die Historie ergeben? (A1, 23.08.2026)

DIE NUTZERFRAGE:

    "Wir sollten einen sauberen Simulationslauf machen ... wir sehen auch aus
     der Historie, ob die Selektion zumindest in der Theorie etwas bringt -
     wie oft gibt es Signale also Empfehlungen, sind diese meist gute Trades -
     je nachdem Spot oder Hebel, u.U. auch noch nach unterschiedlichen Assets
     pruefen - BTC, ETH, Highcap, Midcaps, Smallcaps - in unterschiedlichen
     Marktlagen."

WAS DIESES WERKZEUG TUT - und was es ausdruecklich NICHT tut:

    ES TUT       die AUSWAHL ueber die Historie nachspielen: alle `takt`
                 Handelstage die besten k nach Jahresentwicklung nehmen und
                 messen, was daraus geworden waere.
    ES TUT NICHT die Kette nachspielen. Kein Modell, kein Urteil, kein Stop,
                 kein Ziel. ⚠️ Das ist Absicht: die Auswahl ist eine eigene
                 Stufe, und ihre Wirkung muss ohne alles Nachgelagerte
                 sichtbar sein. Was die Kette daraus macht, ist die naechste
                 Frage - nicht diese.

WAS "EIN GUTER TRADE" HIER HEISST (Nutzervorgabe 23.08.):

    das POTENTIAL - die Bewegung ueber einen festen Horizont, barrierenfrei
    und brutto. NICHT "Ziel vor Stop": das faellt per Konstruktion auf
    1/(1+CRV) und misst unsere eigene Zielregel zurueck.

    Die Kosten stehen DANEBEN, nicht davor: Referenz 0,30 % je Seite fuer die
    Bewertung, Bitpanda 1,50 % je Seite fuer die Geldrechnung.

DIE STUFEN (vorab benannt, nicht gesucht):

    btc      allein          eth      allein
    gross    >= 10 Mrd USD   mittel   1 bis 10 Mrd   klein   < 1 Mrd

⚠️ DIE MARKTKAPITALISIERUNG IST DIE VON HEUTE. Ein Wert, der heute gross ist,
war 2019 klein. Die Einteilung ist deshalb BESCHREIBEND - sie taugt fuer
"verhalten sich grosse Werte anders", nicht fuer "welche Gruppe kaufe ich".

⚠️ UND DER HEBEL IST HIER KEINE EIGENE SPALTE. Er ist faktisch abgeschaltet
(Median 1,10 ueber die Rollen-Signale), und ein zweiter Arm waere eine
Rechnung, keine Messung: ein Hebel h multipliziert Gewinn UND Verlust mit h und
zieht die Finanzierung ab. Was hier steht, ist der Spot-Fall; die Hebelzeile
darunter rechnet ihn nur um und nennt ihre Annahme.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from messe_drift import _reihen, _tafel

RUECKBLICK = 250
K = 2
TAKT = 20                      # Handelstage zwischen zwei Auswahlen (A1c)
SMA_MARKT = 200
GEBUEHR_REFERENZ = 0.003       # je Seite - fuer die BEWERTUNG
GEBUEHR_BETRIEB = 0.015        # je Seite - fuer die GELDRECHNUNG (Bitpanda)
GROSS_AB, MITTEL_AB = 10e9, 1e9


def stufe(symbol: str, kap: float | None) -> str:
    if symbol == "BTC":
        return "btc"
    if symbol == "ETH":
        return "eth"
    if kap is None:
        return "ohne Kap"
    return ("gross" if kap >= GROSS_AB
            else "mittel" if kap >= MITTEL_AB else "klein")


def kapitalisierung(db: str) -> dict:
    import sqlite3
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    aus = {s: k for s, k in c.execute(
        "select symbol, market_cap_usd from price_cache "
        "where market_cap_usd is not null")}
    c.close()
    return aus


def marktzustand(tafel, symbole, t: int) -> float | None:
    if "BTC" not in symbole:
        return None
    i = symbole.index("BTC")
    f = tafel[i, max(0, t - SMA_MARKT + 1):t + 1]
    f = f[~np.isnan(f)]
    if len(f) < SMA_MARKT // 2 or np.isnan(tafel[i, t]):
        return None
    return float(tafel[i, t] / f.mean() - 1.0)


def spiele_nach(tafel, symbole, termine, takt: int, k: int) -> list[dict]:
    """Jede Auswahl ein Datensatz je gewaehltem Wert."""
    n, T = tafel.shape
    aus = []
    for t in range(RUECKBLICK, T - takt, takt):
        gut = (~np.isnan(tafel[:, t]) & ~np.isnan(tafel[:, t - RUECKBLICK])
               & ~np.isnan(tafel[:, t + takt]))
        if gut.sum() < 10:
            continue
        idx = np.where(gut)[0]
        rueck = tafel[idx, t] / tafel[idx, t - RUECKBLICK] - 1.0
        vor = tafel[idx, t + takt] / tafel[idx, t] - 1.0
        if not (np.all(np.isfinite(rueck)) and np.all(np.isfinite(vor))):
            continue
        ordnung = np.argsort(-rueck)
        zustand = marktzustand(tafel, symbole, t)
        markt = float(np.mean(vor))
        for platz, j in enumerate(ordnung[:k], start=1):
            aus.append({"tag": str(termine[t]), "jahr": str(termine[t])[:4],
                        "symbol": symbole[idx[j]], "platz": platz,
                        "rendite": float(vor[j]), "markt": markt,
                        "zustand": zustand})
    return aus


def _zeile(name: str, z: list, breite: int = 22) -> str:
    if not z:
        return f"{name:{breite}} {'-':>8}"
    r = np.array([x["rendite"] for x in z])
    netto_ref = r - 2 * GEBUEHR_REFERENZ
    netto_bet = r - 2 * GEBUEHR_BETRIEB
    m = np.array([x["markt"] for x in z])
    return (f"{name:{breite}} {len(z):8} {100*r.mean():9.2f}% "
            f"{100*np.median(r):9.2f}% {100*m.mean():9.2f}% "
            f"{100*np.mean(netto_ref > 0):8.0f}% "
            f"{100*np.mean(netto_bet > 0):8.0f}%")


def _kopf(was: str, breite: int = 22) -> str:
    return (f"{was:{breite}} {'Signale':>8} {'Mittel':>10} {'Median':>10} "
            f"{'Markt':>10} {'>0 Ref':>9} {'>0 Betr':>9}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    p.add_argument("--takt", type=int, default=TAKT)
    p.add_argument("--k", type=int, default=K)
    args = p.parse_args()

    reihen = _reihen(args.db, args.klasse)
    termine, tafel, symbole = _tafel(reihen)
    kap = kapitalisierung(args.db)
    z = spiele_nach(tafel, symbole, termine, args.takt, args.k)
    if not z:
        print("keine Auswahl moeglich")
        return 1

    jahre = sorted({x["jahr"] for x in z})
    print(f"{args.klasse}: {len(symbole)} Symbole · {termine[0]} bis "
          f"{termine[-1]} · Auswahl alle {args.takt} Handelstage, k={args.k}")
    print(f"{len(z)} Empfehlungen ueber {len(jahre)} Jahre "
          f"= {len(z)/max(1,len(jahre)):.1f} je Jahr\n")
    print("Mass: Bewegung ueber den Takt, BARRIERENFREI und brutto. "
          "'>0' = nach Kosten positiv\n(Ref 0,30 % je Seite fuer die "
          "Bewertung, Betr 1,50 % fuer die Geldrechnung).\n")

    print(_kopf("Gesamt"))
    print(_zeile("alle Empfehlungen", z))
    print(_zeile("  davon Rang 1", [x for x in z if x["platz"] == 1]))
    print(_zeile("  davon Rang 2", [x for x in z if x["platz"] == 2]))

    print("\n" + _kopf("Je Stufe (Kap. heute)"))
    nach = defaultdict(list)
    for x in z:
        nach[stufe(x["symbol"], kap.get(x["symbol"]))].append(x)
    for s in ("btc", "eth", "gross", "mittel", "klein", "ohne Kap"):
        if nach.get(s):
            print(_zeile(s, nach[s]))

    print("\n" + _kopf("Je Marktlage"))
    print(_zeile("BTC ueber 200-Schnitt",
                 [x for x in z if x["zustand"] is not None and x["zustand"] > 0]))
    print(_zeile("BTC unter 200-Schnitt",
                 [x for x in z if x["zustand"] is not None and x["zustand"] <= 0]))

    print("\n" + _kopf("Je Jahr"))
    for j in jahre:
        print(_zeile(j, [x for x in z if x["jahr"] == j]))

    # ---- HEBEL: eine Umrechnung, keine zweite Messung -------------------
    r = np.array([x["rendite"] for x in z])
    print("\n⚠️ HEBEL - Umrechnung, keine eigene Messung. Ein Hebel h "
          "multipliziert Gewinn UND\n   Verlust mit h; die Finanzierung "
          "kommt taeglich dazu.")
    for h in (2.0, 3.0):
        # Finanzierung grob: 0,03 % je Tag auf den geliehenen Teil.
        fin = 0.0003 * args.takt * (h - 1.0)
        netto = h * (r - 2 * GEBUEHR_BETRIEB) - fin
        print(f"   {h:.0f}x: Mittel {100*netto.mean():+6.2f} % · "
              f"positiv {100*np.mean(netto > 0):3.0f} % · "
              f"schlechtester Fall {100*netto.min():+7.2f} %")

    print("\n⚠️ Die Stufen benutzen die Kapitalisierung von HEUTE - "
          "beschreibend, nicht handelbar.\n⚠️ Ueberlebensverzerrung: "
          "gestorbene Werte fehlen, die Zahlen sind eine OBERGRENZE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
