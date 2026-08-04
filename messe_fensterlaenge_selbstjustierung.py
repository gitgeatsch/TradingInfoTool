"""Wie traege soll die Selbstjustierung sein? (2026-08-04)

DIE FRAGE. Die Referenz, gegen die Schwellen kalibriert werden, schwankt
massiv je Marktphase (mechanischer Erwartungswert: -0,197 R im Baerenmarkt
gegen +0,040 R in der Seitwaertsphase, gemessen an 12.421 Einstiegen). Sie
muss also mitwandern. Ueber WIE VIELE Tage soll sie gemittelt werden?

  zu kurz  -> die Schaetzung jagt Rauschen und schlaegt staendig um
  zu lang  -> sie haengt in der alten Phase fest, wenn die neue laengst laeuft

Das ist eine Bias-Varianz-Abwaegung und keine Geschmacksfrage - sie ist
entscheidbar.

DAS VERFAHREN ist eine Walk-Forward-Pruefung, wie sie fuer rollierende
Schaetzer Standard ist:

  1. An jedem Tag t die Referenz aus den LETZTEN W Tagen schaetzen
  2. Dagegen halten, was in den FOLGENDEN H Tagen tatsaechlich eintrat
  3. Der mittlere Fehler ueber alle t bewertet das Fenster W

DIE ENTSCHEIDENDE GEGENPROBE ist nicht "welches W ist am besten", sondern
"ist ueberhaupt eines besser als GAR KEINE Anpassung". Deshalb laeuft ein
fester Wert (Gesamtmittel ueber die volle Historie) als Vergleichsarm mit.
Schlaegt ihn kein Fenster, waere Selbstjustierung reine Bewegung ohne Nutzen -
und das muss das Verfahren sagen koennen.
"""
from __future__ import annotations

import io
import json
import statistics
import sys

from agent.krypto.backward_tracking import gap_bewusster_fill

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"

STOP_REL, CRV, HORIZONT = 0.0394, 2.6, 14      # Median-Parameter der echten Signale
VORHERSAGE_H = 14                              # wie weit voraus die Referenz gelten soll
FENSTER = (7, 14, 21, 30, 45, 60, 90, 120, 180, 270)
MIN_PRO_TAG = 5                                # Mindestzahl Einstiege je Tag


def lade_reihen() -> dict[str, list]:
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    reihen = {}
    for q in ("preishistorie_signal_symbole", "preishistorie_ueberholte_symbole"):
        for s, rr in ((d.get(q) or {}).get("preishistorie_je_symbol") or {}).items():
            g = [p for p in (rr or []) if p.get("currency") == "USD"]
            if len(g) > 60:
                reihen[s] = sorted(g, key=lambda p: str(p["date"])[:10])
    return reihen


def mechanischer_einstieg(reihe: list, i: int) -> float | None:
    """R-Multiple eines LONG-Einstiegs am Schlusskurs von Tag i.

    Identische Konventionen wie das Backward-Tracking (gap_bewusster_fill,
    Stop schlaegt Ziel) - sonst waeren die Zahlen nicht anschlussfaehig."""
    e = reihe[i]["close"]
    if not e or e <= 0:
        return None
    risiko = e * STOP_REL
    stop, ziel = e - risiko, e + risiko * CRV
    for p in reihe[i + 1:i + 2 + HORIZONT]:
        hoch, tief, auf = p["high"], p["low"], p["open"]
        if hoch is None or tief is None:
            continue
        if tief <= stop:
            return (gap_bewusster_fill(stop, auf, True, False) - e) / risiko
        if hoch >= ziel:
            return (gap_bewusster_fill(ziel, auf, False, False) - e) / risiko
    letzter = reihe[min(i + 1 + HORIZONT, len(reihe) - 1)]["close"]
    return None if not letzter else (letzter - e) / risiko


def main() -> int:
    reihen = lade_reihen()
    # Tag -> Liste der R-Werte aller Symbole mit Einstieg an diesem Tag
    je_tag: dict[str, list[float]] = {}
    for reihe in reihen.values():
        for i in range(len(reihe) - HORIZONT - 2):
            r = mechanischer_einstieg(reihe, i)
            if r is not None:
                je_tag.setdefault(str(reihe[i]["date"])[:10], []).append(r)
    tage = sorted(t for t, v in je_tag.items() if len(v) >= MIN_PRO_TAG)
    if len(tage) < 300:
        print(f"nur {len(tage)} auswertbare Tage - zu wenig")
        return 1

    tagesmittel = {t: statistics.fmean(je_tag[t]) for t in tage}
    gesamt = statistics.fmean(list(tagesmittel.values()))
    print("=" * 74)
    print("FENSTERLAENGE DER SELBSTJUSTIERUNG - Walk-Forward")
    print("=" * 74)
    print(f"{len(tage)} Tage mit >= {MIN_PRO_TAG} Einstiegen, "
          f"{tage[0]} .. {tage[-1]}")
    print(f"Referenz global: {gesamt:+.4f} R   "
          f"Tagesstreuung: {statistics.stdev(list(tagesmittel.values())):.4f}")
    print()
    print(f"{'Fenster':>8s} {'n Punkte':>9s} {'mittl. Fehler':>14s} "
          f"{'gegen fest':>12s}")

    idx = {t: k for k, t in enumerate(tage)}
    # Fester Vergleichsarm: immer das Gesamtmittel
    fehler_fest = []
    for t in tage:
        k = idx[t]
        zukunft = tage[k:k + VORHERSAGE_H]
        if len(zukunft) < VORHERSAGE_H:
            continue
        ist = statistics.fmean(tagesmittel[z] for z in zukunft)
        fehler_fest.append(abs(gesamt - ist))
    basis = statistics.fmean(fehler_fest) if fehler_fest else None

    ergebnisse = []
    for W in FENSTER:
        fehler = []
        for t in tage:
            k = idx[t]
            if k < W:
                continue
            zukunft = tage[k:k + VORHERSAGE_H]
            if len(zukunft) < VORHERSAGE_H:
                continue
            schaetzung = statistics.fmean(tagesmittel[z] for z in tage[k - W:k])
            ist = statistics.fmean(tagesmittel[z] for z in zukunft)
            fehler.append(abs(schaetzung - ist))
        if not fehler:
            continue
        m = statistics.fmean(fehler)
        verb = (basis - m) / basis * 100 if basis else 0.0
        ergebnisse.append((W, m, verb, len(fehler)))
        marke = "  <-- besser" if verb > 0 else ""
        print(f"{W:8d} {len(fehler):9d} {m:14.4f} {verb:+11.1f} %{marke}")

    print(f"{'fest':>8s} {len(fehler_fest):9d} {basis:14.4f} "
          f"{0.0:+11.1f} %   (keine Anpassung)")
    print()
    if not ergebnisse:
        print("keine Auswertung moeglich")
        return 1
    bestes = min(ergebnisse, key=lambda e: e[1])
    besser = [e for e in ergebnisse if e[2] > 0]
    if not besser:
        print("BEFUND: KEIN Fenster schlaegt den festen Wert.")
        print("        Selbstjustierung waere Bewegung ohne Nutzen - die")
        print("        Referenz sollte fest bleiben.")
    else:
        print(f"BEFUND: bestes Fenster {bestes[0]} Tage, "
              f"{bestes[2]:+.1f} % gegenueber keiner Anpassung.")
        flach = [e for e in besser if e[1] <= bestes[1] * 1.05]
        if len(flach) > 1:
            print(f"        Flacher Bereich {min(e[0] for e in flach)}-"
                  f"{max(e[0] for e in flach)} Tage (innerhalb 5 % des Besten) -")
            print(f"        im Zweifel das LAENGERE waehlen: mehr Traegheit, "
                  f"weniger Umschalten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
