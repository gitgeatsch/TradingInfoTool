"""Fuer WEN gilt der Befund? (20.08.2026, Umbauplan 120)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DIE LUECKE, DIE DER NUTZER BENANNT HAT. Alles bisher Gemessene lag in EINEM
Topf aus 347 Reihen - BTC und ein Microcap gleich behandelt, Spot und Hebel
gar nicht unterschieden. Fuer ein Signal ist das unbrauchbar: es muss sagen,
FUER WELCHE KLASSE die Aussage gilt.

    Nutzer, 20.08.: *"Es ist erforderlich, die Voraussage auch auf weitere
    Parameter zu teilen - Krypto-Klasse: BTC, Midcap, Smallcap - und
    Handelsstrategie: Hebel oder Spot. Das ist essentiell fuer die
    Zielerreichung."*

⚠️ UND DIE DATEN DEUTEN ES SCHON AN. Kapitel 116 fand den H-Vorsprung
BUCKELFOERMIG ueber den Umsatzbaendern: +0,7 ganz unten, +11,5 in der Mitte,
+3,0 ganz oben. Das wurde dort als "nicht vorab benannte Beobachtung"
abgelegt - es IST diese Frage, nur ohne Namen.

DIE KATEGORIEN, VORAB FESTGELEGT - nennbare Grenzen statt Quantilen, damit
sie in einem Signal stehen koennen:

    BTC      die Referenzreihe, eigene Zeile
    Large    >= 50 Mio. USD Tagesumsatz
    Mid      5 bis 50 Mio.
    Small    < 5 Mio.

⚠️ DER UMSATZ KOMMT VOM ANKER SELBST - Median der letzten 60 Kerzen, NUR
rueckwaerts. Nicht aus der Gesamthistorie des Symbols: sonst wuesste die
Einteilung, wie gross ein Coin SPAETER wurde.

DIE STRATEGIEN:

    Spot     Kosten = 2 x Gebuehr / Stopabstand
    Hebel    zusaetzlich FINANZIERUNG_JE_TAG x Haltedauer / Stopabstand

    Dieselbe Trefferquote ergibt bei Spot und Hebel VERSCHIEDENE
    Erwartungswerte - die Unterscheidung ist keine Etikettierung, sondern
    eine andere Rechnung.

WAS JE ZELLE BERICHTET WIRD:

    Quotendifferenz H gegen Nicht-H, GEBUEHRENFREI  (die eigentliche Frage)
    Nettoerwartungswert in R, zweispaltig (Referenz 0,30 % / Betrieb 1,50 %)
    Fallzahl - damit sichtbar bleibt, worauf die Aussage steht

⚠️ ACHT ZELLEN SIND EIN SUCHPREIS (2.49). Ausgewiesen werden Einzelschwelle
UND Maximum-aus-acht. Eine Kategorie gilt erst als bestaetigt, wenn sie die
strengere nimmt.

⚠️ UND DIE VORSICHTIGE LESART GILT (2.54): ein Fall, der im Horizont nicht
entscheidet, zaehlt als Fehlschlag.

    python messe_klassen.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_marken import CRV, laufe                             # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif         # noqa: E402
from simuliere_bremse import (FINANZIERUNG_JE_TAG,               # noqa: E402
                              SAETZE_ZUM_BERICHTEN)

MIN_FAELLE = 300
BLOCKLAENGE = 250
GRENZE_LARGE = 50_000_000
GRENZE_MID = 5_000_000
KATEGORIEN = ("BTC", "Large", "Mid", "Small")
STRATEGIEN = ("spot", "hebel")


def _kategorie(f) -> str:
    if f["sym"] == "BTC":
        return "BTC"
    u = f["umsatz"] or 0.0
    return ("Large" if u >= GRENZE_LARGE
            else "Mid" if u >= GRENZE_MID else "Small")


def _quote(faelle) -> tuple[int, float]:
    """Vorsichtige Lesart: ein Ablauf zaehlt als Fehlschlag (2.54)."""
    n = len(faelle)
    if not n:
        return 0, float("nan")
    return n, sum(1 for f in faelle if f["ausgang"] == "ziel") / n


def _netto(quote, stop_rel, tage, satz, strategie) -> float:
    """Erwartungswert je Trade in R - mit Finanzierung beim Hebel."""
    brutto = quote * CRV - (1.0 - quote)
    kosten = 2.0 * satz / stop_rel
    if strategie == "hebel":
        kosten += FINANZIERUNG_JE_TAG["hebel"] * tage / stop_rel
    return brutto - kosten


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_klassen.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("FUER WEN GILT DER BEFUND? - Kategorie und Strategie")
    print("=" * 78)
    faelle = [f for f in _reif(laufe(a.db, a.klasse, fortschritt=True),
                               MINDESTALTER) if f["umsatz"]]
    for f in faelle:
        f["kat"] = _kategorie(f)
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    print(f"  {len(faelle)} reife Anker, {len(ent)} entschieden")

    print("\n" + "-" * 78)
    print("DIE KATEGORIEN - H gegen Nicht-H, GEBUEHRENFREI")
    print("-" * 78)
    print(f"  {'Kategorie':10}{'H':>8}{'Quote H':>10}{'Nicht-H':>10}"
          f"{'Quote':>9}{'Vorsprung':>12}{'Stop':>8}{'Tage':>7}")
    zeilen: dict = {}
    for kat in KATEGORIEN:
        teil = [f for f in faelle if f["kat"] == kat]
        h = [f for f in teil if f["frei"] and f["gedeckt"]]
        r = [f for f in teil if not (f["frei"] and f["gedeckt"])]
        nh, qh = _quote(h)
        nr, qr = _quote(r)
        if nh < MIN_FAELLE or nr < MIN_FAELLE:
            print(f"  {kat:10}{nh:8}   zu wenige Faelle")
            continue
        sr = float(np.median([f["stop_relativ"] for f in h]))
        tg = float(np.median([f["tage"] for f in h
                              if f["ausgang"] in ("ziel", "stop")])) \
            if any(f["ausgang"] in ("ziel", "stop") for f in h) else 20.0
        zeilen[kat] = {"n_h": nh, "quote_h": qh, "n_rest": nr,
                       "quote_rest": qr, "vorsprung": qh - qr,
                       "stop_rel": sr, "tage": tg}
        print(f"  {kat:10}{nh:8}{100 * qh:9.1f} %{nr:10}{100 * qr:8.1f} %"
              f"{100 * (qh - qr):+11.1f}{100 * sr:7.1f} %{tg:7.0f}")

    print("\n" + "-" * 78)
    print("NETTOERWARTUNGSWERT JE TRADE (R) - Kategorie x Strategie")
    print("-" * 78)
    print(f"  {'Kategorie':10}{'Strategie':10}"
          + "".join(f"{n + ' H':>20}" for n, _s in SAETZE_ZUM_BERICHTEN)
          + f"{'Nicht-H (Ref.)':>18}")
    netto: dict = {}
    for kat, z in zeilen.items():
        for strat in STRATEGIEN:
            zeile = f"  {kat:10}{strat:10}"
            for _n, satz in SAETZE_ZUM_BERICHTEN:
                w = _netto(z["quote_h"], z["stop_rel"], z["tage"], satz,
                           strat)
                netto[f"{kat}|{strat}|{satz}"] = w
                zeile += f"{w:+19.3f}"
            wr = _netto(z["quote_rest"], z["stop_rel"], z["tage"],
                        SAETZE_ZUM_BERICHTEN[0][1], strat)
            print(zeile + f"{wr:+17.3f}")

    # ---- SCHWELLEN: EINZELN UND MAXIMUM AUS ACHT ------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Kalenderzeit (2.52)")
    print("  Gewuerfelt wird INNERHALB jeder Kategorie (2.50): die Frage ist,")
    print("  ob H DORT etwas beitraegt - nicht, ob die Kategorien sich")
    print("  unterscheiden.")
    print("-" * 78)
    rng = np.random.default_rng(20260907)
    je_kat: dict = {k: [] for k in zeilen}
    hoechste = []
    vorbereitet = {}
    for kat in zeilen:
        teil = [f for f in ent if f["kat"] == kat]
        ziel = np.array([f["ausgang"] == "ziel" for f in teil])
        istH = np.array([f["frei"] and f["gedeckt"] for f in teil])
        ordn: dict = {}
        for pos, f in enumerate(teil):
            ordn.setdefault(f["sym"], []).append((f["i"], pos))
        bl = []
        for vv in ordn.values():
            gr: list = []
            for ii, pos in sorted(vv):
                if not gr or ii - gr[-1][0] >= a.blocklaenge:
                    gr.append([ii, []])
                gr[-1][1].append(pos)
            if len(gr) >= 2:
                bl.append([np.array(g[1]) for g in gr])
        vorbereitet[kat] = (ziel, istH, bl)
        print(f"  {kat:10}{len(bl):5} Reihen mit mindestens zwei Bloecken")
    for _lauf in range(a.blockplacebo):
        beste = -9.9
        for kat, (ziel, istH, bl) in vorbereitet.items():
            gew = ziel.copy()
            for gr in bl:
                alle = np.concatenate(gr)
                gew[alle] = ziel[np.concatenate(
                    [gr[j] for j in rng.permutation(len(gr))])]
            if istH.sum() < MIN_FAELLE or (~istH).sum() < MIN_FAELLE:
                continue
            d = float(gew[istH].mean()) - float(gew[~istH].mean())
            je_kat[kat].append(d)
            beste = max(beste, d)
        if beste > -9.0:
            hoechste.append(beste)
    s_max = float(np.quantile(hoechste, 0.95)) if hoechste else float("nan")
    print(f"\n  {'Kategorie':10}{'gemessen':>12}{'einzeln':>12}"
          f"{'aus acht':>12}{'Urteil':>28}")
    urteile: dict = {}
    for kat, z in zeilen.items():
        if not je_kat[kat]:
            continue
        s1 = float(np.quantile(je_kat[kat], 0.95))
        streu = float(np.std(je_kat[kat])) / math.sqrt(len(je_kat[kat]))
        d = z["vorsprung"]
        if abs(d - s1) < 2 * streu:
            u = "ZU KNAPP (2.48)"
        elif d > s_max:
            u = "TRAEGT (auch aus acht)"
        elif d > s1:
            u = "traegt einzeln, NICHT aus acht"
        else:
            u = "traegt nicht"
        urteile[kat] = {"einzeln": s1, "max_aus_acht": s_max, "urteil": u}
        print(f"  {kat:10}{100 * d:+11.1f}{100 * s1:+11.1f}"
              f"{100 * s_max:+11.1f}{u:>28}")
    print(f"\n  ⚠️ Die Spalte 'aus acht' ist der Preis des Absuchens (2.49).")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "kategorien": zeilen, "netto": netto, "urteile": urteile,
            "grenzen": {"large": GRENZE_LARGE, "mid": GRENZE_MID}},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
