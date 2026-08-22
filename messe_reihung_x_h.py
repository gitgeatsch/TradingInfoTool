# -*- coding: utf-8 -*-
"""Traegt die Reihung ZUSAETZLICH zu H? (22.08.2026, Umbauplan 125)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS - UND ER KAM VOM NUTZER. Die Reihung stand als "traegt nichts" in
der Mail. Nutzereinwand: *"Rangplatz finde ich spannend - wenn dieser nichts
beitraegt sollte man die Frage stellen WARUM und so bauen dass er etwas
beitraegt."* Dazu der zweite Hinweis, der einen Befund verschoben hat: die
hinterlegten Handelskosten waren die RUNDE ZUM BETRIEBSSATZ.

    Vorteil bestes Fuenftel gegenueber Markt      +0,51 %
    gegen Betrieb  3,00 %  ->  -2,50 %   aussichtslos
    gegen Referenz 0,60 %  ->  -0,10 %   verfehlt um ein Zehntel

DIE FRAGE, VORAB FESTGELEGT - UND ES IST GENAU EINE:

    Schlaegt "H UND bestes Fuenftel der Reihung" das blosse H?

⚠️ WARUM GEGEN H UND NICHT GEGEN ALLES. Verglichen wird die Regel mit ihrer
eigenen Grundgesamtheit (Methodik 2.50). Gegen alle Anker gemessen wuerde ich
zum dritten Mal H nachweisen und es der Reihung gutschreiben - genau der
Fehler aus Kapitel 109, der dem Zufallsarm 4,6 Punkte geschenkt hat.

⚠️ UND WARUM UEBERHAUPT EINE KONJUNKTION. Weil die beiden VERSCHIEDENE
Information tragen, und das ist gemessen, nicht vermutet: Kapitel 111 hat die
Momentum-Erklaerung von H zerlegt - 44 % erklaert, +2,3 Punkte bleiben ueber
den Hochabstand hinaus. Die Reihung IST Momentum, H ist Struktur. Nur wenn
die Bestandteile verschiedene Information tragen, kann eine Kombination mehr
sein als ihre Summe (Kapitel 103.1).

⚠️ DER PREIS DES ABSUCHENS (2.49) IST DER GRUND FUER "GENAU EINE FRAGE".
Horizont, Quantilsgrenze und Rueckblickfenster waeren drei weitere Achsen.
Eine vorab benannte Zelle kostet rund 10,2 Punkte Huerde, ein Raster von 300
kostet 20,5. Die Reihung hat 0,10 Punkte Rueckstand aufzuholen - eine Suche
wuerde die Huerde weit ueber alles heben, was hier zu erwarten ist.

    Rueckblick     250 Handelstage   (= drift.RUECKBLICK_TAGE, Produktion)
    Bestes Fuenftel Rang/Zahl <= 0,2 (= drift.saetze, Produktion)

Beide Zahlen sind AUS DER PRODUKTION uebernommen, nicht hier gewaehlt. Damit
gibt es keinen Freiheitsgrad, den ich haette guenstig setzen koennen.

WAS ZUSAETZLICH BERICHTET WIRD - ALS BESCHREIBUNG, NICHT ALS NACHWEIS:

    je Strategie (spot/hebel)   die Finanzierung kostet 0,03 %/Tag und
                                aendert den Breakeven, nicht die Quote
    je Haltedauer-Deckel        20 / 60 / 120 Tage

⚠️ DIESE ZWEI SIND AUSDRUECKLICH KEINE BEFUNDE. Sie stehen mit erhoehter
Huerde da und heissen "Suche", nicht "Nachweis" - wer sie als Ergebnis liest,
hat den Preis des Absuchens nicht bezahlt.

DIE ABBRUCHREGEL:

    Vorsprung ueber der Block-Permutationsschwelle UND ueber der
    Relevanzhuerde von 1,0 Punkt (2.53/2.56)   -> die Reihung wird ein
                                                  Beitrag in
                                                  `wahrscheinlichkeit.py`
    sonst                                      -> sie bleibt `null`, und
                                                  der Nullbefund wird als
                                                  ZERLEGUNG abgelegt (2.51)

⚠️ POSITIVKONTROLLE IST PFLICHT (93 B). Ohne sie heisst "nichts gefunden" nur
"nicht hingesehen".

    python messe_reihung_x_h.py [--laeufe 40] [--placebo]
"""
from __future__ import annotations

import argparse
import io
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from agent.drift import RUECKBLICK_TAGE                       # noqa: E402
from messe_marken import CRV, laufe                           # noqa: E402
from simuliere_bremse import (MAX_TAGE, SAETZE_ZUM_BERICHTEN,  # noqa: E402
                              _reihen_roh, klassen_aus_db)

# ⚠️ AUS DER PRODUKTION, NICHT HIER GEWAEHLT (siehe Kopf).
BESTES_FUENFTEL = 0.20
BLOCKLAENGE = 250
RELEVANZ_PUNKTE = 1.0
MINDEST_SYMBOLE = 10


def entwicklungen(db: str, klasse: str) -> dict:
    """datum -> {symbol: Entwicklung ueber RUECKBLICK_TAGE}.

    ⚠️ NUR RUECKWAERTS. `c[i] / c[i - 250] - 1` an jedem Anker; wer hier
    einen spaeteren Schluss nimmt, misst die Zukunft."""
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    je_datum: dict = {}
    for sym, (c, h, l, v, a, off, d) in roh.items():
        del h, l, v, a, off
        for i in range(RUECKBLICK_TAGE, len(c)):
            frueher, jetzt = float(c[i - RUECKBLICK_TAGE]), float(c[i])
            if frueher > 0 and jetzt > 0:
                je_datum.setdefault(d[i], {})[sym] = jetzt / frueher - 1.0
    return je_datum


def raenge(je_datum: dict) -> dict:
    """(datum, symbol) -> Anteil im Feld, 0,0 = bester.

    ⚠️ NUR TAGE MIT GENUG WERTEN. Ein "Platz 2 von 3" ist kein Rangplatz -
    dieselbe Untergrenze wie `drift.rang` sie in der Produktion zieht."""
    aus = {}
    for datum, werte in je_datum.items():
        if len(werte) < MINDEST_SYMBOLE:
            continue
        sortiert = sorted(werte, key=lambda s: werte[s], reverse=True)
        n = len(sortiert)
        for platz, sym in enumerate(sortiert, 1):
            aus[(datum, sym)] = platz / n
    return aus


def _quote(faelle) -> float:
    return sum(1 for f in faelle if f["ausgang"] == "ziel") / max(len(faelle), 1)


def _netto(faelle, satz: float, finanzierung: float = 0.0) -> float:
    """Erwartungswert je Trade in R, nach Kosten."""
    if not faelle:
        return float("nan")
    q = _quote(faelle)
    sr = float(np.median([f["stop_relativ"] for f in faelle]))
    tage = float(np.median([f["tage"] for f in faelle]))
    return q * CRV - (1 - q) - 2 * satz / sr - finanzierung * tage / sr


def _bloecke(faelle, blocklaenge: int, versatz: int = 0) -> list:
    """Zeitbloecke je Symbol - die Grenzen WANDERN (Methodik 2.47)."""
    ordn: dict = {}
    for pos, f in enumerate(faelle):
        ordn.setdefault(f["sym"], []).append((f["i"], pos))
    aus = []
    for eintraege in ordn.values():
        gr: list = []
        for ii, pos in sorted(eintraege):
            if not gr or (ii + versatz) // blocklaenge != gr[-1][0]:
                gr.append([(ii + versatz) // blocklaenge, []])
            gr[-1][1].append(pos)
        if len(gr) >= 2:
            aus.extend(np.array(g[1]) for g in gr)
    return aus


def schwelle(faelle, ist_r, laeufe: int, blocklaenge: int, saat: int) -> float:
    """Wie gross wird der Vorsprung, wenn die Reihung ZUFAELLIG zugeordnet ist?

    ⚠️ PERMUTIERT WIRD DIE REIHUNG, NICHT DER AUSGANG. Die Frage lautet, ob
    DIESE Zuordnung mehr traegt als eine beliebige - der Ausgang gehoert zum
    Pfad und bleibt, wo er ist."""
    rng = np.random.default_rng(saat)
    ziel = np.array([f["ausgang"] == "ziel" for f in faelle])
    werte = []
    for lauf in range(laeufe):
        bl = _bloecke(faelle, blocklaenge, versatz=int(rng.integers(0, blocklaenge)))
        if len(bl) < 2:
            continue
        getauscht = np.array(ist_r, dtype=bool).copy()
        reihenfolge = rng.permutation(len(bl))
        # Ganze Bloecke vertauschen: die Reihung eines Blocks wandert
        # geschlossen an die Stelle eines anderen.
        quelle = np.concatenate([bl[j] for j in reihenfolge])
        ziel_pos = np.concatenate([bl[j] for j in range(len(bl))])
        n = min(len(quelle), len(ziel_pos))
        getauscht[ziel_pos[:n]] = np.array(ist_r, dtype=bool)[quelle[:n]]
        if getauscht.sum() < 30 or (~getauscht).sum() < 30:
            continue
        werte.append(100 * (ziel[getauscht].mean() - ziel[~getauscht].mean()))
        del lauf
    if not werte:
        raise SystemExit("⚠️ NICHTS ZU PERMUTIEREN - keine brauchbaren Bloecke")
    return float(np.quantile(werte, 0.95)), len(werte)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--laeufe", type=int, default=40)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--placebo", action="store_true",
                    help="Positivkontrolle: einen echten Effekt einpflanzen")
    ap.add_argument("--datei", default="messwerte_reihung_x_h.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("TRAEGT DIE REIHUNG ZUSAETZLICH ZU H?")
    print("  Eine vorab festgelegte Frage. Rueckblick und Quantilsgrenze")
    print("  stammen aus der PRODUKTION, nicht aus dieser Messung.")
    print("=" * 78)

    print("\n1) Anker und H")
    faelle = laufe(a.db, a.klasse, roh_pruefen=False)
    print(f"   {len(faelle)} Anker")

    print("\n2) Die Reihung an jedem Anker")
    rg = raenge(entwicklungen(a.db, a.klasse))
    print(f"   {len(rg)} (Datum, Symbol)-Paare mit Rangplatz")

    # ⚠️ NUR ANKER, DIE BEIDES KENNEN. Wer keinen Rangplatz hat, gehoert in
    # keinen der beiden Arme - sonst vergleicht man auch Datenverfuegbarkeit.
    h = [f for f in faelle if f["frei"] and f["gedeckt"]
         and (f["datum"], f["sym"]) in rg]
    print(f"\n3) H-Anker mit Rangplatz: {len(h)}")
    if len(h) < 300:
        print("   ⚠️ ZU WENIGE - die Frage ist so nicht beantwortbar")
        return 2

    ist_r = [rg[(f["datum"], f["sym"])] <= BESTES_FUENFTEL for f in h]
    if a.placebo:
        # ⚠️ EINE POSITIVKONTROLLE MISST DIE VERSCHIEBUNG, NICHT DEN WERT
        # DANACH. Korrektur vom 22.08.2026, und der Fehler war teuer genug,
        # dass er hier stehenbleibt:
        #
        # Die erste Fassung pflanzte 300 Treffer ein und verglich das
        # ERGEBNIS mit der Zufallsschwelle. Es lag darunter (+0,4 gegen
        # +2,5), und ich haette daraus geschlossen, das Werkzeug sei stumpf.
        # FALSCH. Der eingepflanzte Effekt hob den Wert um genau die
        # erwarteten 6,3 Punkte - aber der ECHTE Effekt ist stark NEGATIV,
        # also landete die Summe trotzdem tief.
        #
        # Eine Positivkontrolle fragt nicht "ist das Ergebnis gross genug",
        # sondern "sehe ich die Aenderung, die ich selbst verursacht habe".
        vorher = 100 * (_quote([f for f, r in zip(h, ist_r) if r])
                        - _quote([f for f, r in zip(h, ist_r) if not r]))
        rng = np.random.default_rng(4711)
        kandidaten = [i for i, (f, r) in enumerate(zip(h, ist_r))
                      if r and f["ausgang"] == "stop"]
        gesetzt = 0
        for i in rng.permutation(kandidaten)[:300]:
            h[int(i)] = dict(h[int(i)], ausgang="ziel")
            gesetzt += 1
        nachher = 100 * (_quote([f for f, r in zip(h, ist_r) if r])
                         - _quote([f for f, r in zip(h, ist_r) if not r]))
        erwartet = 100.0 * gesetzt / max(sum(ist_r), 1)
        print(f"   ⚠️ PLACEBO: {gesetzt} Stops zu Zielen")
        print(f"      Vorsprung vorher   {vorher:+.1f}")
        print(f"      Vorsprung nachher  {nachher:+.1f}")
        print(f"      Verschiebung       {nachher - vorher:+.1f} "
              f"(erwartet {erwartet:+.1f})")
        if abs((nachher - vorher) - erwartet) > 0.5:
            print("      ⚠️ DAS WERKZEUG SIEHT DIE VERSCHIEBUNG NICHT - "
                  "ein Nullbefund waere wertlos")
            return 2
        print("      OK - das Werkzeug sieht den eingepflanzten Effekt")

    mit = [f for f, r in zip(h, ist_r) if r]
    ohne = [f for f, r in zip(h, ist_r) if not r]
    vorsprung = 100 * (_quote(mit) - _quote(ohne))
    print(f"\n{'-' * 78}\nDAS ERGEBNIS - H UND BESTES FUENFTEL GEGEN H ALLEIN\n{'-' * 78}")
    print(f"  {'Arm':30}{'Faelle':>9}{'Quote':>9}")
    print(f"  {'H + bestes Fuenftel':30}{len(mit):9}{100 * _quote(mit):8.1f} %")
    print(f"  {'H, uebriges Feld':30}{len(ohne):9}{100 * _quote(ohne):8.1f} %")
    print(f"  {'Vorsprung':30}{'':9}{vorsprung:+8.1f}")

    sw, n_lauf = schwelle(h, ist_r, a.laeufe, a.blocklaenge, 20260822)
    print(f"\n  Block-Permutation: {n_lauf} brauchbare Laeufe, "
          f"Blocklaenge {a.blocklaenge}")
    print(f"  Schwelle (95 %)                        {sw:+8.1f}")
    print(f"  gemessen                               {vorsprung:+8.1f}")
    print(f"  Relevanzhuerde                         {RELEVANZ_PUNKTE:+8.1f}")

    traegt = vorsprung > sw and vorsprung >= RELEVANZ_PUNKTE
    print(f"\n  -> {'TRAEGT' if traegt else 'traegt NICHT'}")
    # ⚠️ EIN NEGATIVER VORSPRUNG IST KEIN NULLBEFUND, SONDERN EIN BEFUND
    # MIT UMGEKEHRTEM VORZEICHEN - und der gehoert genauso benannt.
    # Die Positivkontrolle laeuft oben und hat hier nichts mehr zu sagen.
    if vorsprung < -RELEVANZ_PUNKTE:
        print(f"  ⚠️ UND ER IST NEGATIV: innerhalb von H schneidet das")
        print(f"     beste Fuenftel der Reihung um {abs(vorsprung):.1f}")
        print(f"     Punkte SCHLECHTER ab als das uebrige Feld.")

    print(f"\n{'-' * 78}\nNETTO JE TRADE (beide Saetze, je Strategie)\n{'-' * 78}")
    print(f"  {'Arm':24}{'Strategie':10}"
          + "".join(f"{n:>20}" for n, _s in SAETZE_ZUM_BERICHTEN))
    for name, menge in (("H + bestes Fuenftel", mit), ("H, uebriges Feld", ohne)):
        for strategie, fin in (("spot", 0.0), ("hebel", 0.0003)):
            zeile = f"  {name:24}{strategie:10}"
            for _n, satz in SAETZE_ZUM_BERICHTEN:
                zeile += f"{_netto(menge, satz, fin):+19.3f}"
            print(zeile)

    # ⚠️ BESCHREIBUNG, KEIN NACHWEIS - der Preis des Absuchens ist nicht
    # bezahlt. Steht hier, weil der Nutzer nach den Zeitraeumen gefragt hat.
    print(f"\n{'-' * 78}")
    print("HALTEDAUER-DECKEL - ⚠️ SUCHE, NICHT NACHWEIS")
    print(f"{'-' * 78}")
    print(f"  {'Deckel':10}{'entschieden':>13}{'Quote H+R':>12}{'Quote H':>10}"
          f"{'Vorsprung':>11}")
    for deckel in (20, 60, MAX_TAGE):
        def kurz(menge):
            return [dict(f, ausgang=(f["ausgang"] if f["tage"] <= deckel
                                     else "abgelaufen")) for f in menge]
        km, ko = kurz(mit), kurz(ohne)
        ent = sum(1 for f in km + ko if f["ausgang"] != "abgelaufen")
        print(f"  {deckel:<10}{100 * ent / len(km + ko):11.1f} %"
              f"{100 * _quote(km):11.1f} %{100 * _quote(ko):9.1f} %"
              f"{100 * (_quote(km) - _quote(ko)):+10.1f}")
    print("  ⚠️ Mit erhoehter Huerde zu lesen (2.49) - drei Werte abgesucht.")
    print("     Die Entscheidungsrate gehoert daneben (2.54): ein kurzer")
    print("     Deckel laesst mehr Faelle unentschieden, und 'abgelaufen'")
    print("     zaehlt in der vorsichtigen Lesart als Fehlschlag.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"anker_h_mit_rang": len(h), "mit": len(mit), "ohne": len(ohne),
             "vorsprung": vorsprung, "schwelle": sw, "laeufe": n_lauf,
             "relevanz": RELEVANZ_PUNKTE, "traegt": bool(traegt),
             "placebo": bool(a.placebo)},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
