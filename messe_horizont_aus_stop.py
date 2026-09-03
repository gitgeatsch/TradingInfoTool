# -*- coding: utf-8 -*-
"""S2 / N-17-0: Den Horizont kennen (03.09.2026).

## Der Auftrag

Aus dem Stufenplan (`Anforderungen_Umbau_28_08.md`, S2): *"Den Horizont
kennen - aus Stop und Volatilitaet die erwartete Zeit bis zur Barriere
ableiten. Zum Zeitpunkt von Stufe 12 ist der Stop bekannt (Reihenfolge:
urteil -> aktion -> geometrie -> entscheider)."* Und ausdruecklich:
*"Schritt 1 ist selbst eine MESSUNG, keine Formel. Die 239 Trades liegen
vor und tragen Stop, CRV und Dauer - die Beziehung ist also messbar statt
zu schaetzen."*

## Vorabfestlegung (vor jeder Messung)

    Frage      Trennt der Stop-Abstand (und/oder das Volatilitaets-
               perzentil) systematisch, wie lange ein Signal bis zur
               Barriere braucht?
    Erwartung  JA in RICHTUNG (ein weiterer Stop braucht laenger, bis
               der Kurs ihn erreicht) - das ist die Grundannahme von
               S2 ueberhaupt, und ohne einen messbaren Zusammenhang
               ist "Horizont aus Stop ableiten" nicht moeglich.
    Maszstab   Spearman-Rangkorrelation (robust gegen die Ausreisser,
               die eine Tagesangabe zwangslaeufig hat: "17 Tage" bei
               einem Median von 2). 90-%-Band ueber Tage-Cluster-
               Bootstrap (2.109 - dieselbe Methode wie in
               messe_g_trefferbilanz.py, aus demselben Grund: die 239
               Faelle verteilen sich auf 21 Kalendertage, nicht
               gleichmaessig).

## Woher die Daten kommen - NICHT die Desktop-DB

Die Desktop-Datenbank hat 0 entschiedene Trades (`quelle_kette='rollen'`
lief nie am Desktop scharf). Die Messung braucht den NB-Export:

    K:\\My Drive\\Claude_Austauschordner\\DB_Backups\\
        tradinginfotool_JJJJ-MM-TT_HHMM.db.gz

Auspacken, `PRAGMA integrity_check`, dann erst messen
(reference_nb_export_und_austauschordner.md).

## Welche Felder

`entry_usd`/`stop_loss_usd` sind fuer diese 239 Zeilen durchgaengig NULL -
die tatsaechlichen Werte stehen in `entry_usd_von`/`stop_loss_usd_von`
(0 fehlende Werte, gegen 239 fehlende in den Nicht-"_von"-Spalten - an
der Quelle geprueft, nicht angenommen). `schwankung_perzentil` fehlt bei
25 von 239 Zeilen; diese werden fuer den Volatilitaets-Teil der Messung
ausgeschlossen, bleiben aber in der Stop-Messung.

    python messe_horizont_aus_stop.py [--db PFAD] [--selbsttest]
"""
from __future__ import annotations

import argparse
import random
import statistics as st
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MISCHUNGEN = 10
BOOTSTRAP = 2000
BAND = 0.90


def lade(db: str) -> list[dict]:
    """Die 239 (oder aktuell mehr) entschiedenen Rollen-Kette-Trades, mit
    Stop-Abstand, Volatilitaetsperzentil, Tag und Kalendertag.

    DIESELBE ABGRENZUNG wie `pruefe_kette_horizonte.dauern()` - ein
    zweites Filterkriterium waere eine zweite Quelle, die auseinanderlaufen
    kann."""
    import sqlite3
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    aus = []
    for row in c.execute(
            "SELECT symbol, entry_usd_von, stop_loss_usd_von, "
            "schwankung_perzentil, created_at, outcome_entschieden_am, "
            "outcome_status FROM signals WHERE quelle_kette='rollen' "
            "AND outcome_status IN ('take_profit_erreicht',"
            "'stop_loss_erreicht')"):
        sym, entry, stop, schwankung, erstellt, entschieden, status = row
        if entry is None or stop is None or not entry:
            continue
        try:
            tag_erstellt = date.fromisoformat(str(erstellt)[:10])
            tag_ende = date.fromisoformat(str(entschieden)[:10])
        except Exception:                                    # noqa: BLE001
            continue
        tage = (tag_ende - tag_erstellt).days
        if not (0 <= tage < 400):
            continue
        aus.append({
            "symbol": sym,
            "stop_relativ": abs(float(entry) - float(stop)) / float(entry),
            "schwankung_perzentil": schwankung,
            "tage": tage,
            "kalendertag": str(erstellt)[:10],
            "take_profit": status == "take_profit_erreicht"})
    return aus


def _rang(werte: list[float]) -> list[float]:
    """Ranguebergabe MIT Bindungen (Mittelrang) - notwendig, weil
    `schwankung_perzentil` gehaeuft denselben Wert traegt (0,0 kommt oft
    vor)."""
    idx = sorted(range(len(werte)), key=lambda i: werte[i])
    raenge = [0.0] * len(werte)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and werte[idx[j + 1]] == werte[idx[i]]:
            j += 1
        mittel = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            raenge[idx[k]] = mittel
        i = j + 1
    return raenge


def spearman(x: list[float], y: list[float]) -> float:
    """Rangkorrelation, ohne scipy - reine Pearson-Korrelation auf den
    Raengen. `None` bei zu wenig Streuung (alle x oder alle y gleich)."""
    if len(x) < 3:
        return None
    rx, ry = _rang(x), _rang(y)
    mx, my = st.mean(rx), st.mean(ry)
    zaehler = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    nx = sum((a - mx) ** 2 for a in rx) ** 0.5
    ny = sum((b - my) ** 2 for b in ry) ** 0.5
    if nx == 0 or ny == 0:
        return None
    return zaehler / (nx * ny)


def cluster_bootstrap(faelle: list[dict], feld: str,
                       n: int = BOOTSTRAP, rng: random.Random = None):
    """90-%-Band der Spearman-Korrelation ueber Tage-Resampling (2.109) -
    Tage mit replacement gezogen, nicht einzelne Faelle, damit die
    Ungleichverteilung (1 bis 37 Faelle/Tag) nicht unterschaetzt wird."""
    rng = rng or random.Random(2026)
    je_tag: dict[str, list[dict]] = {}
    for f in faelle:
        je_tag.setdefault(f["kalendertag"], []).append(f)
    tage = list(je_tag)
    werte = []
    for _ in range(n):
        gezogen = [je_tag[t] for t in
                   (rng.choice(tage) for _ in range(len(tage)))]
        stich = [f for gruppe in gezogen for f in gruppe]
        x = [s[feld] for s in stich]
        y = [s["tage"] for s in stich]
        r = spearman(x, y)
        if r is not None:
            werte.append(r)
    if not werte:
        return None, None
    werte.sort()
    unten = werte[int(len(werte) * (1 - BAND) / 2)]
    oben = werte[int(len(werte) * (1 - (1 - BAND) / 2)) - 1]
    return unten, oben


def terzile(faelle: list[dict], feld: str) -> list[dict]:
    """Drei gleich grosze Gruppen nach `feld`, mit Median-Tagen je Gruppe -
    die Grundlage fuer eine spaetere Nachschlagetabelle (kein Fit, ein
    Nachschlagen: die Vorgabe verlangt eine MESSUNG, keine Formel)."""
    sortiert = sorted(faelle, key=lambda f: f[feld])
    n = len(sortiert)
    drittel = n // 3
    gruppen = [sortiert[:drittel], sortiert[drittel:2 * drittel],
               sortiert[2 * drittel:]]
    aus = []
    for g in gruppen:
        if not g:
            continue
        aus.append({
            "n": len(g),
            "feld_von": g[0][feld], "feld_bis": g[-1][feld],
            "median_tage": st.median(f["tage"] for f in g),
            "mittel_tage": st.mean(f["tage"] for f in g)})
    return aus


def selbsttest() -> bool:
    """Zwei synthetische Welten: eine mit echtem Zusammenhang (Stop und
    Tage steigen gemeinsam, mit Rauschen), eine ohne (Tage zufaellig,
    unabhaengig vom Stop). Die Messung muss BEIDE richtig unterscheiden -
    sonst prueft sie nicht, was sie zu pruefen behauptet."""
    rng = random.Random(7)
    ok = True

    # Welt 1: echter Zusammenhang - Tage = 20 * stop_relativ + Rauschen
    welt1 = []
    for i in range(200):
        stop = rng.uniform(0.01, 0.15)
        tage = max(0, round(20 * stop + rng.gauss(0, 1.5)))
        welt1.append({"stop_relativ": stop, "tage": tage,
                      "kalendertag": f"2026-01-{1 + i % 20:02d}"})
    r1 = spearman([f["stop_relativ"] for f in welt1],
                  [f["tage"] for f in welt1])
    print(f"  Selbsttest Welt 1 (echter Zusammenhang): r={r1:+.3f}"
          .replace(".", ","))
    if not (r1 is not None and r1 > 0.4):
        print("  ✖ FEHLER: Welt 1 haette einen deutlichen Zusammenhang "
              "zeigen muessen")
        ok = False

    # Welt 2: kein Zusammenhang - Tage unabhaengig vom Stop
    welt2 = []
    for i in range(200):
        stop = rng.uniform(0.01, 0.15)
        tage = rng.randint(0, 10)
        welt2.append({"stop_relativ": stop, "tage": tage,
                      "kalendertag": f"2026-01-{1 + i % 20:02d}"})
    r2 = spearman([f["stop_relativ"] for f in welt2],
                  [f["tage"] for f in welt2])
    print(f"  Selbsttest Welt 2 (kein Zusammenhang): r={r2:+.3f}"
          .replace(".", ","))
    if not (r2 is not None and abs(r2) < 0.2):
        print("  ✖ FEHLER: Welt 2 haette nahe Null liegen muessen")
        ok = False

    print("  ✔ Selbsttest bestanden" if ok else "  ✖ SELBSTTEST FEHLGESCHLAGEN")
    return ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--selbsttest", action="store_true")
    a = p.parse_args()

    if a.selbsttest:
        ok = selbsttest()
        return 0 if ok else 1

    print("=" * 78)
    print("S2 / N-17-0: DEN HORIZONT KENNEN")
    print("=" * 78)
    faelle = lade(a.db)
    if not faelle:
        print("  ⚠️ keine entschiedenen Trades in %s" % a.db)
        print("     (am Desktop erwartet - die Produktions-DB liegt am "
              "NB; DB_Backups im Austauschordner verwenden)")
        return 1
    print(f"  {len(faelle)} entschiedene Trades, "
          f"{len(set(f['kalendertag'] for f in faelle))} Kalendertage")

    print()
    print("-" * 78)
    print("STOP-ABSTAND GEGEN DAUER")
    print("-" * 78)
    x = [f["stop_relativ"] for f in faelle]
    y = [f["tage"] for f in faelle]
    r = spearman(x, y)
    unten, oben = cluster_bootstrap(faelle, "stop_relativ")
    print(f"  Spearman r = {r:+.3f}   90-%-Band [{unten:+.3f} .. {oben:+.3f}]"
          .replace(".", ","))
    for t in terzile(faelle, "stop_relativ"):
        print(f"    n={t['n']:3d}  Stop {t['feld_von']*100:5.2f}–"
              f"{t['feld_bis']*100:5.2f} %   Median {t['median_tage']:.1f} "
              f"Tage · Mittel {t['mittel_tage']:.1f}".replace(".", ","))

    schw = [f for f in faelle if f["schwankung_perzentil"] is not None]
    if schw:
        print()
        print("-" * 78)
        print("VOLATILITAETSPERZENTIL GEGEN DAUER "
              f"({len(schw)} von {len(faelle)} Faellen)")
        print("-" * 78)
        xs = [f["schwankung_perzentil"] for f in schw]
        ys = [f["tage"] for f in schw]
        rs = spearman(xs, ys)
        us, os_ = cluster_bootstrap(schw, "schwankung_perzentil")
        print(f"  Spearman r = {rs:+.3f}   90-%-Band [{us:+.3f} .. {os_:+.3f}]"
              .replace(".", ","))
        for t in terzile(schw, "schwankung_perzentil"):
            print(f"    n={t['n']:3d}  Perzentil {t['feld_von']:.2f}–"
                  f"{t['feld_bis']:.2f}   Median {t['median_tage']:.1f} "
                  f"Tage · Mittel {t['mittel_tage']:.1f}".replace(".", ","))

    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
