"""Wirkt unsere Marktphase INVERS? (20.08.2026, Umbauplan 114)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. Kapitel 110 lieferte eine Zahl, die oekonomisch nicht sein
duerfte: SHORTS schneiden im "Baermarkt" AM SCHLECHTESTEN ab (-15,3 gegen
-7,0 im Bullenmarkt). Und Kapitel 108 zeigt dasselbe von der anderen Seite -
LONG-Anker liegen im Baermarkt bei -2,2 und im Bullenmarkt bei -3,3, also im
Baermarkt BESSER.

Beides zusammen ergibt nur einen Sinn, wenn das Etikett NACHLAEUFT:
`_marktphase` misst die Indexbewegung ueber die VERGANGENEN 250 Tage. "Baer"
heisst dann "der Markt IST gefallen", nicht "der Markt faellt" - und nach
einem langen Fall folgt oft die Gegenbewegung.

⚠️ WARUM DAS UEBER DIESE MESSUNG HINAUS WICHTIG IST. Die Marktphase steckt in
JEDER Lagenaussage dieses Projekts: in der Phasenprobe, die die Kapitel 101,
102, 103 und 109 zu Fall gebracht hat, und in der Regel aus 109. Bedeutet
"baer" das Gegenteil dessen, was man beim Lesen annimmt, sind diese Urteile
zwar nicht falsch - aber sie sagen etwas anderes, als bisher dabeisteht.

DIE FRAGE, VORAB FESTGELEGT - und sie wird AN DER WURZEL gestellt, nicht am
Barrierensystem:

    P1  Ist die kuenftige Indexbewegung nach dem Etikett "baer" GROESSER als
        nach "bulle"?

        ja   -> das Etikett ist ein Kontraindikator. Jede Lagenaussage des
                Projekts ist umzudeuten, keine ist zu verwerfen.
        nein -> die Zahlen aus 108/110 haben eine andere Ursache, und die
                ist dann zu suchen.

    Horizonte 20, 60 und 120 Handelstage; 120 ist der Hauptwert, weil er dem
    Vorwaertsfenster des Barrierensystems entspricht (MAX_TAGE).

⚠️ EINE ZWEITE MESSUNG GEGEN DIE ZUSAMMENSETZUNG. Der Produktionsindex
normiert jede Reihe auf ihre EIGENE erste Kerze (`c[j] / c[0]`) und mittelt
ueber die, die es an dem Tag gibt - von 2 Reihen (2017) auf 347 (2026). Eine
neu gelistete Reihe steigt mit 1,0 ein, waehrend alte bei 5,0 stehen; der
Mittelwert faellt dann, OHNE dass der Markt gefallen waere. Genau die Falle
aus Kapitel 93 A2.

    Deshalb laeuft alles ZWEIMAL: einmal mit dem Produktionsindex, einmal mit
    einem zusammensetzungsfreien - dem verketteten Median der TAGESrenditen
    derer, die an beiden Tagen da sind. Stimmen beide ueberein, haengt der
    Befund am Markt; widersprechen sie sich, haengt er am Indexbau.

⚠️ DIE KONTROLLE MUSS ZUR UEBERLAPPUNG PASSEN (2.47). Vorwaertsfenster von
120 Tagen auf taeglichen Etiketten ueberlappen um mehr als 99 % - gewuerfelt
werden ZEITBLOECKE, nicht einzelne Tage.

⚠️ UND DER ABSTAND GEHOERT DANEBEN (2.53). Ein Unterschied kann statistisch
echt und wirtschaftlich belanglos sein; ausgewiesen wird die Rendite in
Prozent, nicht nur das Urteil.

    python messe_phase_invers.py [--blockplacebo 120]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from simuliere_bremse import (MAX_TAGE, PHASE_SCHWELLE,         # noqa: E402
                              _marktphase, _reihen_roh,
                              klassen_aus_db)

HORIZONTE = (20, 60, MAX_TAGE)
LAGEN = ("bulle", "seitwaerts", "baer")
BLOCKLAENGE = 250
MIN_TAGE = 100


def _index_produktion(roh: dict) -> tuple[list, np.ndarray]:
    """Genau wie `_marktphase` ihn baut - c[j]/c[0], gemittelt."""
    reihen: dict = {}
    for _sym, (c, _h, _l, _v, _a, _off, d) in roh.items():
        for j, tag in enumerate(d):
            reihen.setdefault(tag, []).append(c[j] / c[0])
    tage = sorted(reihen)
    return tage, np.array([float(np.mean(reihen[t])) for t in tage])


def _index_zusammensetzungsfrei(roh: dict) -> tuple[list, np.ndarray]:
    """BTC allein - der einzige Index ohne Zusammensetzungsproblem.

    ⚠️ ZWEI EIGENE FEHLVERSUCHE, BEIDE VERWORFEN. Naheliegend waere ein
    verketteter Querschnitt der Tagesrenditen gewesen. Beide Fassungen sind
    unbrauchbar, und zwar messbar:

        aus MEDIANEN verkettet     -100 %   ueber die ganze Reihe
        aus MITTELN verkettet  +194.392 %

    Der Median-Tag ist bei schiefer Verteilung negativ, waehrend ein
    Portfolio steigt - verkettete Mediane sind schlicht kein Index. Und das
    Mittel wird von Ausreissern erschlagen: +28,6 % Tagesrendite im Schnitt
    stammen aus Neulistungen und Mikrowerten, nicht aus dem Markt.

    BTC hat das Problem nicht: EINE Reihe, durchgehend ab 2017-08-17, keine
    Zusammensetzung, die wandert. Als Referenz fuer die Marktlage ist das die
    uebliche Wahl - und hier die einzige, die ohne Konstruktionsannahme
    auskommt."""
    for sym, (c, _h, _l, _v, _a, _off, d) in roh.items():
        if sym == "BTC":
            return list(d), np.array([float(x) for x in c])
    raise SystemExit("BTC fehlt in dieser Datenbank - ohne Referenzreihe "
                     "ist die Gegenprobe nicht moeglich.")


def _vorwaerts(index: np.ndarray, h: int) -> np.ndarray:
    """Rendite ueber die naechsten h Tage; NaN, wo sie nicht existiert."""
    aus = np.full(len(index), np.nan)
    if len(index) > h:
        aus[:-h] = index[h:] / index[:-h] - 1.0
    return aus


def _blockschwelle(werte: np.ndarray, gruppe: np.ndarray, tage_idx: np.ndarray,
                   laeufe: int, blocklaenge: int,
                   rng) -> tuple[float, float, int]:
    """95-%-Schwelle fuer (Mittel baer - Mittel bulle) unter Zeitblock-Tausch."""
    gut = np.isfinite(werte)
    w, g, ti = werte[gut], gruppe[gut], tage_idx[gut]
    bloecke, start = [], None
    akt: list = []
    for pos, idx in enumerate(ti):
        if start is None or idx - start >= blocklaenge:
            if akt:
                bloecke.append(np.array(akt))
            start, akt = idx, []
        akt.append(pos)
    if akt:
        bloecke.append(np.array(akt))
    if len(bloecke) < 2:
        return float("nan"), float("nan"), len(bloecke)
    alle = np.concatenate(bloecke)
    zieh = []
    for _lauf in range(laeufe):
        neu = np.concatenate([bloecke[j] for j in
                              rng.permutation(len(bloecke))])
        gew = np.empty_like(w)
        gew[alle] = w[neu]
        mb, mu = gew[g == 2].mean(), gew[g == 0].mean()
        zieh.append(mb - mu)
    return (float(np.quantile(zieh, 0.95)),
            float(np.std(zieh)) / math.sqrt(len(zieh)), len(bloecke))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=120)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_phase_invers.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WIRKT UNSERE MARKTPHASE INVERS?")
    print("  Vorhergesagt: nach dem Etikett 'baer' steigt der Index MEHR")
    print("  als nach 'bulle' - dann misst das Etikett die Vergangenheit.")
    print("=" * 78)
    roh = _reihen_roh(a.db, a.klasse, klassen_aus_db(a.db))
    etikett = _marktphase(roh, 250, PHASE_SCHWELLE)
    print(f"  {len(roh)} Reihen, {len(etikett)} etikettierte Tage")

    rng = np.random.default_rng(20260901)
    ergebnis: dict = {}
    for bau, name in ((_index_produktion, "Produktionsindex (c[j]/c[0])"),
                      (_index_zusammensetzungsfrei,
                       "zusammensetzungsfrei (BTC allein)")):
        tage, index = bau(roh)
        print("\n" + "-" * 78)
        print(name.upper())
        print("-" * 78)
        gruppe = np.array([{"bulle": 0, "seitwaerts": 1, "baer": 2}.get(
            etikett.get(t, "unbekannt"), -1) for t in tage])
        tage_idx = np.arange(len(tage))
        print(f"  {'Horizont':12}" + "".join(f"{lg:>14}" for lg in LAGEN)
              + f"{'baer - bulle':>16}{'Schwelle':>12}{'Urteil':>16}")
        for h in HORIZONTE:
            vw = _vorwaerts(index, h)
            zeile, mittel = f"  {h:<4} Tage   ", {}
            for k, lg in enumerate(LAGEN):
                m = (gruppe == k) & np.isfinite(vw)
                mittel[lg] = float(vw[m].mean()) if m.sum() >= MIN_TAGE \
                    else float("nan")
                zeile += (f"{100 * mittel[lg]:+13.1f}" if mittel[lg] == mittel[lg]
                          else f"{'zu wenige':>14}")
            d = mittel["baer"] - mittel["bulle"]
            s, streu, nb = _blockschwelle(vw, gruppe, tage_idx,
                                          a.blockplacebo, a.blocklaenge, rng)
            urteil = ("zu wenige" if d != d or s != s else
                      "ZU KNAPP (2.48)" if abs(d - s) < 2 * streu else
                      "INVERS" if d > s else "nicht invers")
            zeile += (f"{100 * d:+15.1f}" if d == d else f"{'':>16}")
            zeile += (f"{100 * s:+11.1f}" if s == s else f"{'':>12}")
            print(zeile + f"{urteil:>16}")
            ergebnis[f"{name[:12]}_{h}"] = {
                "mittel": mittel, "diff": d, "schwelle": s, "bloecke": nb,
                "urteil": urteil}
        print(f"  ({nb} Zeitbloecke fuer die Kontrolle)")

    print("\n" + "=" * 78)
    print("LESEHILFE: die Zahlen sind Renditen des Marktindex in Prozent,")
    print("nicht Trefferquoten. 'INVERS' heisst: nach einem gefallenen Markt")
    print("steigt er staerker als nach einem gestiegenen - das Etikett sagt")
    print("dann etwas ueber die VERGANGENHEIT, nicht ueber die Zukunft.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            ergebnis, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
