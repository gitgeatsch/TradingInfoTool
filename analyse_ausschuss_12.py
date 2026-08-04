"""Phase 1.2: die Ausschuss-Hypothese an echten Daten, erste Haelfte.

DIE FRAGE. Gibt es unter den vom Gate GEBLOCKTEN Signalen eine ueber
Einstiegsmerkmale identifizierbare Teilmenge, deren Ergebnis mindestens dem
der DURCHGELASSENEN entspricht? Wenn ja, laesst sich das Gate gezielt fuer
genau diese Faelle oeffnen - mehr Signale UND bessere.

VORGEHEN nach Zielgroessen_und_Erfolgsmasse.md 7.3:
  - gesucht wird NUR auf der ersten Haelfte (bis 22.07.)
  - die zweite Haelfte bleibt fuer 1.3 unangetastet und wird hier nicht
    einmal geladen - sonst waere sie kein Holdout mehr
  - je Tier getrennt, mit demselben Verfahren (43 gemeinsame Merkmale)

Benannte Pruefaelle, die frueher schon einmal aus dem Plan gefallen waren:
  1.2a Komplementaritaet trigger_score x confidence_pct (nur Hebel)
  1.2b CRV als Merkmal - beantwortet die offene Schwellenfrage 2,0 gegen 4,0
       mit Falschtrefferkontrolle statt als Einzelmessung

Lauf: python analyse_ausschuss_12.py
"""
from __future__ import annotations

import io
import json
import sys

import numpy as np

from agent.krypto.ausschuss_merkmale import baue_merkmale
from agent.krypto.ausschuss_suche import (
    ICC_OBERGRENZE, ausschuss_suche, intraklassen_korrelation,
    pruefe_merkmalsliste,
)
from agent.krypto.backward_tracking import _RESOLVED_OUTCOMES

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
TRENNDATUM = "2026-07-23"        # erste Haelfte: created_at < TRENNDATUM
NULL_ZIEHUNGEN = 2000            # einmalige Auswertung, hier darf es genau sein


def lade():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    stamm = d.get("watchlist_stammdaten") or {}
    if not stamm:
        print("HINWEIS: watchlist_stammdaten fehlt im Export (Schritt a noch")
        print("         nicht deployed) - Spot bleibt ein Sammeltopf.")
    return d, stamm


def population(rows, veto: bool, bis_datum: str):
    feld = "veto_outcome_status" if veto else "outcome_status"
    crv_feld = ("veto_outcome_realisiertes_crv" if veto
                else "outcome_realisiertes_crv")
    raus = []
    for r in rows:
        if r.get("take_profit_usd_von") is None:
            continue
        if bool(r.get("risk_veto")) != veto:
            continue
        if r.get(feld) not in _RESOLVED_OUTCOMES:
            continue
        if str(r.get("created_at") or "")[:10] >= bis_datum:
            continue          # zweite Haelfte: Holdout, hier nicht anfassen
        if r.get(crv_feld) is None:
            continue
        raus.append(r)
    return raus


def auswerten(name: str, rows_alle: list[dict]) -> None:
    print()
    print("=" * 78)
    print(f"TIER: {name}")
    print("=" * 78)

    durchgelassen = population(rows_alle, False, TRENNDATUM)
    geblockt = population(rows_alle, True, TRENNDATUM)
    if len(geblockt) < 30:
        print(f"  nur {len(geblockt)} geblockte aufgeloeste Faelle vor "
              f"{TRENNDATUM} - fuer eine Suche zu duenn.")
        print(f"  (durchgelassen: {len(durchgelassen)})")
        return

    y_ref = np.array([r["outcome_realisiertes_crv"] for r in durchgelassen], dtype=float)
    y = np.array([r["veto_outcome_realisiertes_crv"] for r in geblockt], dtype=float)
    symbole = np.array([r["symbol"] for r in geblockt])

    referenz = float(y_ref.mean()) if len(y_ref) else float("nan")
    print(f"  durchgelassen: n={len(y_ref):3d}   EW {referenz:+.3f} R")
    print(f"  geblockt:      n={len(y):3d}   EW {y.mean():+.3f} R"
          f"   aus {len(np.unique(symbole))} Symbolen")

    X, namen, bericht = baue_merkmale(geblockt)
    print(f"  Merkmale: {len(namen)}")
    for zeile in bericht[:3]:
        print(f"    {zeile}")
    if len(bericht) > 3:
        print(f"    ... und {len(bericht)-3} weitere Hinweise")

    # PFLICHTPRUEFUNG vor der Suche: keine getarnten Symbol-Kennungen
    verstoesse = pruefe_merkmalsliste(namen, X, symbole)
    if verstoesse:
        print(f"  {len(verstoesse)} Merkmale als Symbol-Kennung erkannt und "
              f"entfernt (ICC >= {ICC_OBERGRENZE}):")
        for v in verstoesse[:6]:
            print(f"    {v}")
        raus = {v.split(" (")[0] for v in verstoesse}
        behalten = [j for j, nm in enumerate(namen) if nm not in raus]
        X, namen = X[:, behalten], [namen[j] for j in behalten]
        print(f"  verbleibend: {len(namen)} Merkmale")

    if not namen:
        print("  keine zulaessigen Merkmale - Abbruch fuer dieses Tier")
        return

    erg = ausschuss_suche(X, y, symbole, namen, null_ziehungen=NULL_ZIEHUNGEN)
    print()
    print(f"  Hypothesenraum: {erg.hypothesen} Schnitte "
          f"({len(namen)} Merkmale x {erg.n_gesamt-1})")
    print(f"  Nullziehungen:  {erg.null_ziehungen}")
    if erg.bester is None:
        print("  kein gueltiger Kandidat")
        return

    k = erg.bester
    print()
    print(f"  BESTER KANDIDAT: {k.beschreibung}")
    print(f"    Teilmenge n={k.n} ({k.n/erg.n_gesamt*100:.0f} %)   "
          f"EW {k.ew:+.3f} R   Rest {k.ew_rest:+.3f} R")
    print(f"    gegen durchgelassene ({referenz:+.3f} R): "
          f"{k.ew - referenz:+.3f} R")
    print(f"    p = {erg.p_wert:.4f}   (Max-Statistik, symbolgeblockt)")
    for w in erg.warnungen:
        print(f"    WARNUNG: {w}")
    if erg.top_symbol:
        print(f"    Beitrags-Konzentration: {erg.top_symbol} "
              f"{erg.top_symbol_anteil*100:.0f} %")

    print()
    bestanden = (erg.p_wert is not None and erg.p_wert <= 0.05
                 and k.ew >= referenz)
    if bestanden:
        print("  ERGEBNIS: Kandidat besteht beide Bedingungen "
              "(signifikant UND >= durchgelassene).")
        print("            -> 1.3 auf dem Holdout pruefen.")
    elif erg.p_wert is not None and erg.p_wert > 0.05:
        print(f"  ERGEBNIS: NICHT signifikant (p={erg.p_wert:.3f}). Der beste "
              "aus")
        print(f"            {erg.hypothesen} Kandidaten ist nicht besser als "
              "der beste,")
        print("            den Zufall bei dieser Symbolstruktur liefert.")
    else:
        print(f"  ERGEBNIS: signifikant, aber EW {k.ew:+.3f} R unter der "
              f"Referenz {referenz:+.3f} R.")

    # --- 1.2a / 1.2b: die benannten Pruefaelle ---------------------------
    print()
    print("  Benannte Pruefaelle:")
    for wunsch, label in (("confidence_pct", "1.2a Konfidenz"),
                          ("trigger_score", "1.2a Screening-Score"),
                          ("z_crv", "1.2b CRV")):
        if wunsch not in namen:
            print(f"    {label:24s} nicht unter den Merkmalen")
            continue
        j = namen.index(wunsch)
        icc = intraklassen_korrelation(X[:, j], symbole)
        r = np.corrcoef(X[:, j], y)[0, 1]
        print(f"    {label:24s} ICC {icc:.3f}   Korrelation mit R {r:+.3f}")


def main() -> int:
    d, stamm = lade()
    print("=" * 78)
    print(f"PHASE 1.2 - Ausschuss-Hypothese, erste Haelfte (< {TRENNDATUM})")
    print("=" * 78)
    print("Die zweite Haelfte wird hier NICHT geladen - sie ist der Holdout")
    print("fuer 1.3 und waere nach einem Blick keiner mehr.")

    auswerten("hebel", d["hebel_signals"])

    spot = d["spot_signals"]
    if stamm:
        klassen = sorted({stamm.get(r["symbol"], {}).get("assetklasse", "unbekannt")
                          for r in spot})
        for kl in klassen:
            auswerten(f"spot/{kl}",
                      [r for r in spot
                       if stamm.get(r["symbol"], {}).get("assetklasse",
                                                         "unbekannt") == kl])
    else:
        auswerten("spot (Sammeltopf)", spot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
