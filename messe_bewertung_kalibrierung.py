# -*- coding: utf-8 -*-
"""N-37: Ist die Bewertung kalibriert? (05.09.2026)

Vorabfestlegung: `Anforderungen_Umbau_28_08.md`, Abschnitt **N-37**.

## Die Frage

    Liefert ein hoeheres Potential tatsaechlich eine hoehere Trefferquote?

Vorbedingung fuer jede Hebelabstufung (N-36/H-2): Kelly ohne kalibriertes
mue ist eine Formel ohne Eingabe.

## Die vier Fallen und ihre Behandlung - alle vorab benannt

1 ZIRKULARITAET   Die Stufen sind IN-SAMPLE gefittet. Auf denselben
                  Ankern zu messen ist per Konstruktion wahr.
                  -> Stufen auf der ERSTEN Haelfte fitten, Kalibrierung
                     auf der ZWEITEN pruefen.

2 FORM (2.85)     Das Potential gilt fuer ein BARRIERENSYSTEM, nicht fuer
                  eine Rendite nach festen Tagen.
                  -> Barrieren-Ausgang ueber die bestehende, validierte
                     `messe_zielregel.ergebnisse()` (Ziel e+2r, Stop e-r,
                     Stop gewinnt bei Gleichstand, Datenbrueche entfernt).
                     Gezaehlt werden nur ENTSCHIEDENE Anker.

3 ARITHMETIK      quote = 1/(1+CRV) = 33,3 % steht per Konstruktion fest.
                  Die Behauptung ist ein Shift von 4,5 Prozentpunkten
                  (0,000 -> 33,3 % · 0,080 -> 36,0 % · 0,133 -> 37,8 %).
                  -> DAS ist die Pruefgroesse, nicht "traegt/traegt nicht".

4 MACHT           Vorab gerechnet: ~1.800 entschiedene Anker je Gruppe.
                  Bindend ist die Blockzahl (~32), nicht die Ankerzahl.

## Die echten Funktionen - nichts nachgebaut

    Barriere    messe_zielregel.ergebnisse()
    Fuenftel    dieselbe Konvention wie `marktrang._rang/_fuenftel`
                (aufsteigend, 0 = niedrigster Rohwert, min(int(r*5),4))
    Potential   agent.potential.rechne()  - mit VORUEBERGEHEND ersetzten
                Stufen (die aus der ersten Haelfte), danach zurueckgesetzt

    python messe_bewertung_kalibrierung.py [--selbsttest]
"""
from __future__ import annotations

import dataclasses
import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402
import rechne_kandidaten_beitrag as RB                       # noqa: E402
from agent import potential as PT                            # noqa: E402
from agent import wahrscheinlichkeit as W                    # noqa: E402

CRV = 2.0
BLOCK = 90
ZIEHUNGEN = 2000
MISCHUNGEN = 10        # 2.104: eine Ziehung ist kein Nullpunkt
SAAT = 20260905
VARIANTE = "ZIEL 2,0"          # genau der registrierte CRV-Wert
STOP_RELATIV = 0.05            # nur fuer die Kostenebene; potential.rechne
                               # ruft gebuehrenfrei, der Wert wirkt nicht
                               # auf `quote` - siehe Selbsttest 0


def _fuenftel_je_tag(je_tag: dict) -> dict:
    """{tag: {sym: 0..4}} - dieselbe Konvention wie `marktrang`.

    ⚠️ AUFSTEIGEND: Fuenftel 0 ist der NIEDRIGSTE Rohwert. Wer das dreht,
    dreht die Beitraege ins Gegenteil, ohne dass etwas anschlaegt (die
    Warnung steht so in `wahrscheinlichkeit.BEITRAEGE`).
    """
    aus = {}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 2:
            continue
        sortiert = sorted(zeilen, key=lambda x: x["kennzahl"])
        n = len(sortiert) - 1
        aus[tag] = {x["sym"]: min(int((i / n) * 5), 4)
                    for i, x in enumerate(sortiert)}
    return aus


def _mit_stufen(funding_stufen, turnover_stufen):
    """Ersetzt die registrierten Stufen VORUEBERGEHEND durch die gefitteten.

    ⚠️ Damit rechnet weiterhin die ECHTE `potential.rechne()` - nur die
    Tabelle kommt aus der ersten Haelfte statt aus der Registrierung. Eine
    eigene Nachbildung der Formel waere der Fehler, den dieses Projekt
    schon dreimal gemacht hat.
    """
    neu = []
    for b in W.BEITRAEGE:
        if b.merkmal == "funding_fuenftel" and b.stufen:
            neu.append(dataclasses.replace(b, stufen=tuple(funding_stufen)))
        elif b.merkmal == "turnover_fuenftel" and b.stufen:
            neu.append(dataclasses.replace(b, stufen=tuple(turnover_stufen)))
        else:
            neu.append(b)
    return tuple(neu)


def potential_je_anker(fu5: dict, tu5: dict, tag: str, sym: str):
    """Das Potential dieses Ankers - ueber die ECHTE Funktion."""
    merkmale = {}
    f = (fu5.get(tag) or {}).get(sym)
    t = (tu5.get(tag) or {}).get(sym)
    if f is not None:
        merkmale["funding_fuenftel"] = f
    if t is not None:
        merkmale["turnover_fuenftel"] = t
    if not merkmale:
        return None
    try:
        return PT.rechne(crv=CRV, stop_relativ=STOP_RELATIV, klasse="krypto",
                         instrument="spot", strategie="einstieg",
                         merkmale=merkmale)
    except Exception:                                        # noqa: BLE001
        return None


def _quote_und_band(gruppen: dict, rng) -> None:
    """Je Potentialstufe: realisierte Quote, mit Block-Bootstrap ueber TAGE.

    ⚠️ Ueber Tage, nicht ueber Anker (2.107): das Vorwaertsfenster ist
    60 Tage lang, benachbarte Anker teilen sich Kerzen.
    """
    print("  %-12s %10s %10s %12s   %s"
          % ("Potential", "entsch.", "Quote", "vorhergesagt", "Band"))
    for p in sorted(gruppen):
        je_tag = gruppen[p]
        tage = sorted(je_tag)
        treffer = sum(sum(v) for v in je_tag.values())
        n = sum(len(v) for v in je_tag.values())
        if n < 200:
            print("  %+.3f R      %10d   zu wenige entschiedene Anker" % (p, n))
            continue
        quote = treffer / n
        boot = []
        for _ in range(ZIEHUNGEN // 4):
            zieh = [tage[i] for i in rng.integers(0, len(tage), len(tage))]
            tr = sum(sum(je_tag[t]) for t in zieh)
            nn = sum(len(je_tag[t]) for t in zieh)
            if nn:
                boot.append(tr / nn)
        u, o = np.quantile(boot, [0.025, 0.975]) if boot else (np.nan, np.nan)
        vorher = (p + 1.0) / (1.0 + CRV)      # quote = (Potential+1)/(1+CRV)
        print("  %+.3f R      %10d   %8.1f%%   %10.1f%%   [%.1f%% .. %.1f%%]"
              % (p, n, 100 * quote, 100 * vorher, 100 * u, 100 * o))


def _steigung_kern(gruppen: dict, tage) -> float:
    """DIE EINE Steigungsrechnung - von `_steigung` und `_steigung_wert`
    gleichermassen benutzt, damit es keine zweite Fassung gibt."""
    x, y, w = [], [], []
    for p, je_tag in gruppen.items():
        tr = sum(sum(je_tag[t]) for t in tage if t in je_tag)
        nn = sum(len(je_tag[t]) for t in tage if t in je_tag)
        if nn >= 50:
            x.append(p)
            y.append(tr / nn)
            w.append(nn)
    if len(x) < 3:
        return float("nan")
    x, y, w = np.array(x), np.array(y), np.array(w, float)
    xm = np.average(x, weights=w)
    ym = np.average(y, weights=w)
    var = np.average((x - xm) ** 2, weights=w)
    if var <= 0:
        return float("nan")
    return float(np.average((x - xm) * (y - ym), weights=w) / var)


def _steigung_wert(gruppen: dict) -> float:
    """Nur die Zahl, ohne Band und ohne Ausgabe - fuer die Mischungen."""
    tage = sorted({t for g in gruppen.values() for t in g})
    return _steigung_kern(gruppen, tage) if len(tage) >= 60 else float("nan")


def _steigung(gruppen: dict, rng) -> None:
    """Die eine Zahl, an der die Vorabfestlegung haengt: steigt die Quote?

    Gewichtete Regression der Quote auf das Potential, Block-Bootstrap
    ueber Kalendertage. Erwartung bei perfekter Kalibrierung: Steigung
    1/(1+CRV) = 0,333 Quote-Punkte je R Potential.
    """
    alle_tage = sorted({t for g in gruppen.values() for t in g})
    if len(alle_tage) < 60:
        print("    zu wenige Tage (%d)" % len(alle_tage))
        return

    def steig(tage):
        return _steigung_kern(gruppen, tage)

    echt = steig(alle_tage)
    boot = [steig([alle_tage[i] for i in rng.integers(0, len(alle_tage),
                                                     len(alle_tage))])
            for _ in range(ZIEHUNGEN // 4)]
    boot = [b for b in boot if np.isfinite(b)]
    if len(boot) < 50:
        print("    Bootstrap zu duenn")
        return
    u, o = np.quantile(boot, [0.025, 0.975])
    urteil = ("KALIBRIERT-Richtung" if u > 0
              else ("UMGEKEHRT" if o < 0 else "nicht trennbar"))
    print("    Steigung %+.3f Quote-Punkte je R  [%+.3f .. %+.3f]  %s"
          % (echt, u, o, urteil))
    print("    (bei perfekter Kalibrierung erwartet: %+.3f)" % (1.0 / (1.0 + CRV)))
    return echt


def baue_gruppen(zeilen, tage_je_sym, fu5, tu5, nur_tage=None,
                 mische=None, pflanze=None):
    """{Potentialstufe: {tag: [0/1, ...]}} - nur ENTSCHIEDENE Anker."""
    gruppen: dict = defaultdict(lambda: defaultdict(list))
    for z in zeilen:
        sym, i = z["sym"], z["i"]
        tage = tage_je_sym.get(sym)
        if not tage or i >= len(tage):
            continue
        tag = tage[i]
        if nur_tage is not None and tag not in nur_tage:
            continue
        wert = z.get(VARIANTE)
        # ⚠️ NUR ENTSCHIEDENE: exakt +CRV (Ziel) oder exakt -1 (Stop).
        if wert is None:
            continue
        if abs(wert - CRV) < 1e-9:
            treffer = 1
        elif abs(wert + 1.0) < 1e-9:
            treffer = 0
        else:
            continue
        p = potential_je_anker(fu5, tu5, tag, sym)
        if p is None:
            continue
        wr = round(p.wert_r, 3)
        if mische is not None:
            wr = None            # wird unten je Tag neu verteilt
            gruppen["_roh"][tag].append((treffer, round(p.wert_r, 3)))
            continue
        if pflanze is not None and wr >= pflanze[0]:
            treffer = 1 if np.random.default_rng(
                abs(hash((sym, tag))) % 2**31).random() < pflanze[1] else treffer
        gruppen[wr][tag].append(treffer)
    if mische is None:
        return {k: dict(v) for k, v in gruppen.items()}
    # Zufallskontrolle: die Potentialwerte JE TAG mischen, Treffer bleiben
    aus: dict = defaultdict(lambda: defaultdict(list))
    for tag, paare in gruppen["_roh"].items():
        werte = [w for _t, w in paare]
        mische.shuffle(werte)
        for (t, _w), w2 in zip(paare, werte):
            aus[w2][tag].append(t)
    return {k: dict(v) for k, v in aus.items()}


def _stufen_direkt(merkmal: str, stufe: int) -> float:
    """Die Punkte dieses Fuenftels - AUS DER TABELLE, ohne die Formel.

    Nur fuer den Selbsttest: die Wahrheit muss unabhaengig von der
    geprueften Funktion entstehen.
    """
    for b in W.BEITRAEGE:
        if b.merkmal == merkmal and b.stufen:
            return float(b.stufen[max(0, min(int(stufe), len(b.stufen) - 1))])
    return 0.0


def selbsttest() -> bool:
    """Zwei Welten mit BEKANNTER Antwort - vor dem teuren Lauf.

    A  das Potential haengt NICHT mit dem Ausgang zusammen
       -> die Steigung darf NICHT gefunden werden
    B  ein hoeheres Potential liefert wirklich eine hoehere Quote
       -> sie MUSS gefunden werden, und zwar nahe am gepflanzten Wert
    """
    ok = True
    for welt, echt_kalibriert in (("A (kein Zusammenhang)", False),
                                  ("B (echte Kalibrierung)", True)):
        rng = np.random.default_rng(7)
        gruppen: dict = defaultdict(lambda: defaultdict(list))
        for t in range(400):
            tag = "t%03d" % t
            for i in range(60):
                # Potentialstufen wie sie real vorkommen
                p = float(rng.choice([0.000, 0.020, 0.043, 0.078, 0.133]))
                q = ((p + 1.0) / 3.0) if echt_kalibriert else (1.0 / 3.0)
                gruppen[round(p, 3)][tag].append(
                    1 if rng.random() < q else 0)
        g = {k: dict(v) for k, v in gruppen.items()}
        print("  SELBSTTEST %s" % welt)
        _steigung(g, np.random.default_rng(3))
    print("  ⚠️ Erwartung: A 'nicht trennbar', B nahe +0,333 und TRAEGT")

    # ---- Selbsttest 2: die KETTE, nicht nur die Statistik --------------
    #
    # ⚠️ Der erste Teil prueft nur `_steigung`. Die Kette davor -
    # Fuenftel-Nachschlag, ECHTER `potential.rechne()`-Aufruf,
    # Entschieden-Filter, Gruppierung - bliebe ungeprueft. Genau diese
    # Luecke hat gestern zugeschlagen (F-212, Fehler 5).
    print()
    print("  SELBSTTEST 2 — die ganze Kette mit bekannter Wahrheit")
    rng = np.random.default_rng(11)
    fu5, tu5, zeilen, tage_je_sym = {}, {}, [], {}
    for si in range(40):
        sym = "S%02d" % si
        tage_je_sym[sym] = ["t%03d" % t for t in range(400)]
    for t in range(400):
        tag = "t%03d" % t
        fu5[tag], tu5[tag] = {}, {}
        for si in range(40):
            sym = "S%02d" % si
            f = int(rng.integers(0, 5)); u = int(rng.integers(0, 5))
            fu5[tag][sym] = f
            tu5[tag][sym] = u
            # ⚠️⚠️ DIE WAHRHEIT WIRD UNABHAENGIG ERZEUGT - aus der
            # Stufentabelle DIREKT, nicht ueber `potential_je_anker`.
            #
            # Erste Fassung erzeugte sie mit derselben Funktion, die
            # geprueft wird: bei einem Fehler waeren Wahrheit und Messung
            # gleich falsch, und der Test haette trotzdem bestanden.
            # Derselbe Zirkel wie in F-206/F-212.
            zuschlag = _stufen_direkt("funding_fuenftel", f) +                        _stufen_direkt("turnover_fuenftel", u)
            q = (1.0 / 3.0) + zuschlag / 100.0
            zeilen.append({"sym": sym, "i": t,
                           VARIANTE: (CRV if rng.random() < q else -1.0)})
    g = baue_gruppen(zeilen, tage_je_sym, fu5, tu5)
    print("    Stufen gefunden: %d" % len(g))
    _steigung(g, np.random.default_rng(5))
    print("    ⚠️ Erwartung: nahe +0,333 und TRAEGT - sonst ist die Kette kaputt")
    return ok


def main() -> int:
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    print("%d Krypto-Reihen (F-204-gefiltert)" % len(reihen))

    print("Barrieren-Ausgaenge ueber messe_zielregel.ergebnisse()...", flush=True)
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker" % len(zeilen))

    print("Fuenftel je Kalendertag...", flush=True)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    fu_roh = K.baue(reihen, "funding", F.lade_funding(), horizont=20)
    tu_roh = K.baue(reihen, "turnover", menge, horizont=20)
    fu5, tu5 = _fuenftel_je_tag(fu_roh), _fuenftel_je_tag(tu_roh)
    print("  Funding %d Tage · Turnover %d Tage" % (len(fu5), len(tu5)))

    # ---- der SPLIT: erste Haelfte fitten, zweite pruefen ----------------
    alle = sorted(set(fu5) | set(tu5))
    mitte = alle[len(alle) // 2]
    erste = {t for t in alle if t < mitte}
    zweite = {t for t in alle if t >= mitte}
    print()
    print("  SPLIT bei %s  ·  erste Haelfte %d Tage · zweite %d Tage"
          % (mitte, len(erste), len(zweite)))

    print()
    print("=" * 92)
    print("KONTROLLE 1 — REPRODUKTION: treffen die Stufen aus der ersten")
    print("Haelfte die registrierten Werte?")
    print("=" * 92)
    fit = {}
    for name, roh, registriert in (
            ("funding", fu_roh, (+0.82, +1.30, +0.12, -0.54, -1.70)),
            ("turnover", tu_roh, (+3.15, +0.83, +0.22, -1.79, -2.40))):
        h1 = {t: z for t, z in roh.items() if t in erste}
        _w, punkte, _s = RB.beitragstabelle(h1)
        fit[name] = punkte if punkte else list(registriert)
        print("  %-9s erste Haelfte %s" % (name, " ".join("%+5.2f" % x for x in fit[name])))
        print("  %-9s registriert   %s" % ("", " ".join("%+5.2f" % x for x in registriert)))
        if punkte:
            ab = max(abs(a - b) for a, b in zip(punkte, registriert))
            print("            groesste Abweichung %.2f Punkte  %s"
                  % (ab, "OK" if ab < 1.5 else "⚠️ GROSS - Split evtl. nicht repraesentativ"))
        print()

    alt = W.BEITRAEGE
    W.BEITRAEGE = _mit_stufen(fit["funding"], fit["turnover"])
    try:
        rng = np.random.default_rng(SAAT)
        g2 = baue_gruppen(zeilen, tage_je_sym, fu5, tu5, nur_tage=zweite)
        print("=" * 92)
        print("DAS ERGEBNIS — zweite Haelfte, out-of-sample")
        print("=" * 92)
        print("  unterscheidbare Potentialstufen: %d" % len(g2))
        print()
        _quote_und_band(g2, rng)
        print()
        print("  DIE PRUEFGROESSE — steigt die Quote mit dem Potential?")
        echt_steigung = _steigung(g2, rng)

        print()
        print("=" * 92)
        print("KONTROLLE 2 — ZUFALL: Potentialwerte je Tag gemischt")
        print("=" * 92)
        # ⚠️⚠️ MEHRERE MISCHUNGEN (2.104). Die erste Fassung nahm EINE
        # Ziehung und meldete -0,055 "UMGEKEHRT" - fast das Spiegelbild
        # des echten Werts. Eine einzelne Ziehung ist kein Nullpunkt,
        # sondern eine Zufallszahl.
        werte = []
        for s in range(MISCHUNGEN):
            gz = baue_gruppen(zeilen, tage_je_sym, fu5, tu5, nur_tage=zweite,
                              mische=np.random.default_rng(SAAT + 100 + s))
            v = _steigung_wert(gz)
            if np.isfinite(v):
                werte.append(v)
                print("    Mischung %2d: %+.3f" % (s + 1, v))
        if werte:
            a = np.array(werte)
            print("    ---")
            print("    Mittel ueber %d Mischungen: %+.3f  (Spanne %+.3f .. %+.3f)"
                  % (a.size, a.mean(), a.min(), a.max()))
            print("    ECHT war %+.3f - liegt er ausserhalb dieser Spanne?  %s"
                  % (echt_steigung,
                     "JA" if (echt_steigung > a.max() or echt_steigung < a.min())
                     else "NEIN -> der Befund ist NICHT vom Zufall zu trennen"))

        print()
        print("=" * 92)
        print("KONTROLLE 3 — BASISRATE: liegt die schwaechste Stufe bei 33,3 %?")
        print("=" * 92)
        if g2:
            p0 = min(g2)
            je = g2[p0]
            n = sum(len(v) for v in je.values())
            q = sum(sum(v) for v in je.values()) / max(n, 1)
            print("  schwaechste Stufe %+.3f R:  Quote %.1f %%  (erwartet ~33,3 %%)"
                  % (p0, 100 * q))
            print("  %s" % ("OK - die Barrieren-Rechnung stimmt" if abs(q - 1/3) < 0.04
                            else "⚠️ WEICHT AB - erst die Barriere klaeren, nicht die Bewertung"))
    finally:
        W.BEITRAEGE = alt
    return 0


if __name__ == "__main__":
    sys.exit(main())
