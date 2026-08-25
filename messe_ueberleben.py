"""Wie stark verzerrt das Ueberleben? (20.08.2026, Umbauplan 121)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. Kapitel 120 fand die Grundquote der Smallcaps bei 35,1 % - hoeher
als die der Largecaps (27,9 %) und hoeher als der driftfreie Wert von 33,3 %.
Das ist erklaerungsbeduerftig, und die naheliegende Erklaerung ist die
UEBERLEBENSVERZERRUNG: die 347 Reihen sind Paare, die HEUTE handeln. Ein
Smallcap, der eingestellt wurde, fehlt - genau in der kleinsten und
ausfallanfaelligsten Kategorie.

WAS JETZT DAZUKOMMT. Binance fuehrt 209 eingestellte USDT-Paare (Status
`BREAK`), und der Kline-Endpunkt liefert fuer sie weiterhin Daten. 176 davon
haben genug Historie - das ist ein Drittel der neuen Gesamtstichprobe von 523
Reihen.

⚠️ `BREAK` IST NICHT GLEICH GESCHEITERT. Darin stecken auch Umbenennungen
(BCC -> BCH, VEN -> VET) und Wechsel der Notierungswaehrung. Die Gruppe ist
heterogen - sie ist trotzdem unvergleichlich besser als ihr vollstaendiges
Fehlen, denn bisher lag die Verzerrung bei 100 %.

⚠️ EINE ENTSCHEIDUNG, VORAB GETROFFEN UND BEGRUENDET. Eine eingestellte Reihe
ENDET. Ein Anker kurz vor dem Ende hat sein Vorwaertsfenster nicht mehr.

    Solche Anker VERWERFEN  -> genau der terminale Absturz flieget raus, und
                               die Verzerrung waere wieder drin, nur
                               versteckter.
    Als FEHLSCHLAG werten   -> ein Delisting bedeutet Zwangsausstieg, meist
                               mit Verlust.

Genommen wird die zweite - die vorsichtige Lesart (2.54), konsistent mit allen
Messungen seit Kapitel 117, und der einzige Weg, der die Verzerrung nicht
durch die Hintertuer zurueckholt.

DIE ZWEI FRAGEN, VORAB FESTGELEGT:

    S1  Wie stark aendert sich die GRUNDQUOTE je Kategorie, wenn die
        eingestellten Reihen dazukommen?
        Vorhergesagt: Small am staerksten - dort liegen die meisten
        Ausfaelle, und dort lag die Quote ueber dem driftfreien Wert.

    S2  Wie stark aendert sich H's VORSPRUNG?
        Vorhergesagt: wenig - die Verzerrung trifft beide Arme, weil H
        INNERHALB derselben Reihen gegen Nicht-H verglichen wird.

    Trifft S1 zu und S2 nicht, ist der Befund aus 120 in seiner RELATIVEN
    Aussage stabil und in seiner ABSOLUTEN korrigiert.
    Trifft auch S2 zu, war der Vorsprung selbst teilweise Ueberlebenseffekt -
    und dann muss die beste Zeile weg.

    python messe_ueberleben.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sqlite3
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_klassen import (KATEGORIEN, MIN_FAELLE, STRATEGIEN,   # noqa: E402
                           _kategorie, _netto, _quote)
from messe_marken import laufe                                   # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif          # noqa: E402
from simuliere_bremse import SAETZE_ZUM_BERICHTEN                 # noqa: E402


def _status(db: str) -> dict:
    """Symbol -> 'handelnd' / 'eingestellt'. Fehlt die Tabelle, ist die
    Messung nicht durchfuehrbar - dann lieber abbrechen als so tun."""
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
            aus = dict(c.execute(
                "SELECT symbol, status FROM messreihen_status"))
    except sqlite3.Error:
        raise SystemExit(
            "Tabelle `messreihen_status` fehlt. Ohne sie laesst sich "
            "handelnd nicht von eingestellt trennen - erst "
            "`lade_messreihen.py --status BREAK --schreiben` laufen lassen.")
    if not aus:
        raise SystemExit("`messreihen_status` ist leer.")
    return aus


def _schneide(sortiert: dict, versatz: int, laenge: int,
              verfahren: str = "greedy") -> list:
    """Bloecke je Reihe. `versatz` verschiebt ALLE Grenzen (Methodik 2.47).

    `versatz = 0` liefert exakt die alte, feste Einteilung: neuer Block,
    sobald `laenge` Einheiten seit dem letzten Blockbeginn vergangen sind.
    Sonst liegen die Schnitte auf dem Raster `versatz + n * laenge` -
    dieselbe Blocklaenge, andere Lage.
    """
    aus = []
    for vv in sortiert.values():
        gr: list = []
        for ii, pos in vv:
            if verfahren == "raster" or versatz:
                schl = (ii - versatz) // laenge
                if not gr or gr[-1][0] != schl:
                    gr.append([schl, []])
            elif not gr or ii - gr[-1][0] >= laenge:
                gr.append([ii, []])
            gr[-1][1].append(pos)
        if len(gr) >= 2:
            aus.append([np.array(g[1]) for g in gr])
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--blocklaenge", type=int, default=250)
    # S3 (25.08.2026, Methodik 2.75): siehe bewerte_neu.py. Regel 2.47
    # verlangt wandernde Grenzen; dieses Werkzeug setzte sie fest und
    # hat damit die Kategorienurteile aus Kapitel 121 erzeugt.
    ap.add_argument("--blockgrenzen", choices=("fest", "wandernd"),
                    default="fest")
    # Siehe bewerte_neu.py: "greedy" schneidet ab dem ersten Anker weiter,
    # "raster" auf festen Linien. Getrennt schaltbar, damit der Vergleich
    # nicht zwei Aenderungen zugleich enthaelt.
    ap.add_argument("--blockverfahren", choices=("greedy", "raster"),
                    default="greedy")
    ap.add_argument("--datei", default="messwerte_ueberleben.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WIE STARK VERZERRT DAS UEBERLEBEN?")
    print("  347 handelnde Reihen gegen 523 mit den eingestellten.")
    print("=" * 78)
    status = _status(a.db)
    faelle = [f for f in _reif(laufe(a.db, a.klasse, fortschritt=True),
                               MINDESTALTER) if f["umsatz"]]
    for f in faelle:
        f["kat"] = _kategorie(f)
        f["st"] = status.get(f["sym"], "unbekannt")
    n_e = sum(1 for f in faelle if f["st"] == "eingestellt")
    print(f"  {len(faelle)} reife Anker, davon {n_e} aus eingestellten "
          f"Reihen ({100 * n_e / len(faelle):.0f} %)")

    # ---- S1 + S2 --------------------------------------------------------
    print("\n" + "-" * 78)
    print("S1/S2 - GRUNDQUOTE UND H-VORSPRUNG, mit und ohne die Ausfaelle")
    print("-" * 78)
    print(f"  {'Kategorie':10}{'':4}{'H':>7}{'Quote H':>10}{'Quote Rest':>12}"
          f"{'Vorsprung':>11}")
    tabelle: dict = {}
    for kat in KATEGORIEN:
        for name, wo in (("nur handelnd",
                          lambda f: f["st"] == "handelnd"),
                         ("ALLE", lambda f: True)):
            teil = [f for f in faelle if f["kat"] == kat and wo(f)]
            h = [f for f in teil if f["frei"] and f["gedeckt"]]
            r = [f for f in teil if not (f["frei"] and f["gedeckt"])]
            nh, qh = _quote(h)
            nr, qr = _quote(r)
            if nh < MIN_FAELLE or nr < MIN_FAELLE:
                print(f"  {kat:10}{name:14}{nh:7}   zu wenige")
                continue
            sr = float(np.median([f["stop_relativ"] for f in h]))
            tg = float(np.median([f["tage"] for f in h]))
            tabelle[f"{kat}|{name}"] = {
                "n_h": nh, "quote_h": qh, "n_rest": nr, "quote_rest": qr,
                "vorsprung": qh - qr, "stop_rel": sr, "tage": tg}
            print(f"  {kat:10}{name:14}{nh:7}{100 * qh:9.1f} %"
                  f"{100 * qr:11.1f} %{100 * (qh - qr):+10.1f}")
        a_, b_ = tabelle.get(f"{kat}|nur handelnd"), tabelle.get(f"{kat}|ALLE")
        if a_ and b_:
            print(f"  {'':10}{'-> Aenderung':14}{'':7}"
                  f"{100 * (b_['quote_h'] - a_['quote_h']):+9.1f}  "
                  f"{100 * (b_['quote_rest'] - a_['quote_rest']):+10.1f}  "
                  f"{100 * (b_['vorsprung'] - a_['vorsprung']):+9.1f}")

    # ---- NETTOERWARTUNGSWERT AUF DER VOLLEN STICHPROBE ------------------
    print("\n" + "-" * 78)
    print("NETTOERWARTUNGSWERT JE TRADE (R) - auf ALLEN 523 Reihen")
    print("-" * 78)
    print(f"  {'Kategorie':10}{'Strat.':8}"
          + "".join(f"{n + ' H':>20}" for n, _s in SAETZE_ZUM_BERICHTEN)
          + f"{'Nicht-H (Ref.)':>18}")
    netto: dict = {}
    for kat in KATEGORIEN:
        z = tabelle.get(f"{kat}|ALLE")
        if not z:
            continue
        for strat in STRATEGIEN:
            zeile = f"  {kat:10}{strat:8}"
            for _n, satz in SAETZE_ZUM_BERICHTEN:
                w = _netto(z["quote_h"], z["stop_rel"], z["tage"], satz,
                           strat)
                netto[f"{kat}|{strat}|{satz}"] = w
                zeile += f"{w:+19.3f}"
            wr = _netto(z["quote_rest"], z["stop_rel"], z["tage"],
                        SAETZE_ZUM_BERICHTEN[0][1], strat)
            print(zeile + f"{wr:+17.3f}")

    # ---- SCHWELLE AUF DER VOLLEN STICHPROBE -----------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION auf ALLEN Reihen - {a.blockplacebo} Laeufe")
    print("-" * 78)
    # ⚠️ VORSICHTIGE LESART (2.54): ALLE Anker zaehlen, ein Ablauf gilt als
    # Fehlschlag. Genau deshalb steht hier kein Filter - bei eingestellten
    # Reihen ist der Ablauf die Regel, nicht die Ausnahme.
    ent = list(faelle)
    rng = np.random.default_rng(20260908)
    je_kat: dict = {}
    hoechste = []
    vorbereitet = {}
    for kat in KATEGORIEN:
        if f"{kat}|ALLE" not in tabelle:
            continue
        teil = [f for f in ent if f["kat"] == kat]
        ziel = np.array([f["ausgang"] == "ziel" for f in teil])
        istH = np.array([f["frei"] and f["gedeckt"] for f in teil])
        ordn: dict = {}
        for pos, f in enumerate(teil):
            ordn.setdefault(f["sym"], []).append((f["i"], pos))
        srt = {s: sorted(vv) for s, vv in ordn.items()}
        bl = _schneide(srt, 0, a.blocklaenge, a.blockverfahren)
        vorbereitet[kat] = (ziel, istH, srt, bl)
        je_kat[kat] = []
        print(f"  {kat:10}{len(bl):5} Reihen mit mindestens zwei Bloecken")
    # ⚠️ Eigener Zufallsstrom fuer den Versatz - liefe er aus `rng`, haetten
    # die beiden Varianten verschiedene Permutationsfolgen, und der Vergleich
    # mischte zwei Aenderungen (siehe bewerte_neu.py).
    rngv = np.random.default_rng(20260909)
    for _lauf in range(a.blockplacebo):
        beste = -9.9
        versatz = (int(rngv.integers(1, a.blocklaenge + 1))
                   if a.blockgrenzen == "wandernd" else 0)
        for kat, (ziel, istH, srt, bl_fest) in vorbereitet.items():
            bl = (_schneide(srt, versatz, a.blocklaenge, a.blockverfahren)
                  if versatz else bl_fest)
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
    print(f"\n  {'Kategorie':10}{'gemessen':>12}{'einzeln':>11}"
          f"{'aus acht':>11}{'Urteil':>28}")
    urteile: dict = {}
    for kat in KATEGORIEN:
        z = tabelle.get(f"{kat}|ALLE")
        if not z or not je_kat.get(kat):
            continue
        s1 = float(np.quantile(je_kat[kat], 0.95))
        streu = float(np.std(je_kat[kat])) / math.sqrt(len(je_kat[kat]))
        d = z["vorsprung"]
        u = ("ZU KNAPP (2.48)" if abs(d - s1) < 2 * streu
             else "TRAEGT (auch aus acht)" if d > s_max
             else "traegt einzeln, NICHT aus acht" if d > s1
             else "traegt nicht")
        urteile[kat] = {"einzeln": s1, "max": s_max, "urteil": u}
        print(f"  {kat:10}{100 * d:+11.1f}{100 * s1:+10.1f}"
              f"{100 * s_max:+10.1f}{u:>28}")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "tabelle": tabelle, "netto": netto, "urteile": urteile,
            "anteil_eingestellt": n_e / len(faelle)},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
