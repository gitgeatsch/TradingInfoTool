# -*- coding: utf-8 -*-
"""Backtest (2026-08-01, Nutzer-Fund "CoinGecko-Tagesverbrauch zu hoch,
u.U. muessen wir einschraenken" - siehe Memory
project_coingecko_kontingent_tracking.md fuer den urspruenglichen 223/Tag-
Fixboden): rekonstruiert rueckwirkend, wie viele CoinGecko-Calls
`agent/krypto/marktscan.py::run_scan()` in der Vergangenheit TATSAECHLICH
verursacht hat, und was zwei Restriktions-Optionen an Ersparnis gebracht
haetten - BEVOR irgendein Produktivcode geaendert wird (gleicher
Zwischen-Checkpoint wie backtest_ueberholt_erkennung.py, Memory
feedback_backtest_first_hard_guarantee.md).

Kontext (Live-Code-Analyse derselben Session): `run_scan()` kostet pro Lauf
- 5 Calls fuer `fetch_top_gainers()` (5 Marktkap.-Seiten) + 1 Call fuer
`get_trending()` (FIX, 6 Calls) - plus VARIABEL:
- 1 `get_simple_prices()`-Call je Trending-Coin, der NICHT schon unter den
  Top-Gainern war (discovery_source == "trending" in den gespeicherten
  Kandidaten).
- 2 `backfill_history()`-Calls (USD+EUR, Default-Waehrungen) je Stufe-A-
  Ueberlebendem (`_try_backfill_snapshot()`, marktscan.py:397) - das sind
  die gespeicherten Kandidaten mit `score_gesamt is not None`.
- 1 `get_coin_ath_change_percentage()`-Call je JUNGEM Stufe-A-Ueberlebenden
  (Alter <= config.yaml marktscan.filter.ath_abstand_junger_coin_max_alter_
  tage) - das Kandidaten-Alter wird NICHT dauerhaft gespeichert, dieser
  Anteil kann aus den Exportdaten NICHT rekonstruiert werden und wird hier
  bewusst NICHT mitgerechnet (P-10: fehlend statt geraten) - siehe
  Ergebnis-Ausgabe fuer den expliziten Hinweis, keine stille Untertreibung.

Zwei geprüfte Restriktions-Optionen:
- USD-only: backfill_history() nur mit currencies=("usd",) statt Default
  ("usd","eur") - EUR wird fuer den technischen Snapshot (RSI/MACD/EMA)
  nicht gebraucht, siehe Uebernahmequoten-Argument unten.
- Top-N-Deckel (kombiniert mit USD-only): nur die N besten Stufe-A-
  Ueberlebenden (nach den bereits gespeicherten Scores sortiert) bekommen
  ueberhaupt einen Backfill-Call, der Rest bleibt ohne technischen Score
  (identisch zum heutigen Verhalten fuer Nicht-Stufe-A-Kandidaten).

Zusatz-Kennzahl: Uebernahmequote (wie oft wird ein Marktscan-Kandidat
tatsaechlich in die echte Watchlist uebernommen, `status ==
"nutzer_behalten_manuell_uebernommen"`) - Begruendung fuer USD-only, siehe
Ergebnis-Ausgabe.

Liest dieselbe notebook_diagnose.json wie die anderen backtest_*.py-Skripte
(Sektion `rohdaten_fuer_backtest.marktscan_alle_kandidaten`, `discovered_at`/
`discovery_source`/`score_gesamt`/`status` je gespeichertem Rohkandidaten -
siehe extract_notebook_diagnose.py::_rohdaten_fuer_backtest()-Docstring).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

NOTEBOOK_EXPORT_PFAD = Path(
    r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json"
)

# Gap zwischen zwei Kandidaten-Discovery-Zeitstempeln, ab dem ein neuer Scan-
# Lauf beginnt - marktscan_job laeuft cron-fest um 04:00/16:00 Uhr (12h
# Abstand), 300 Minuten (5h) trennt das sauber von der Innerhalb-eines-Laufs-
# Streuung (Sekunden bis wenige Minuten, live per Gap-Histogramm bestaetigt:
# groesster Gap INNERHALB eines Laufs < 10 Min, kleinster Gap ZWISCHEN zwei
# Laeufen > 700 Min).
RUN_GAP_MINUTEN = 300

FIXKOSTEN_JE_LAUF = 6  # 5x fetch_top_gainers()-Seiten + 1x get_trending()

TOP_N_VARIANTEN = [5, 10, 15]


def _lade_kandidaten() -> list[dict]:
    rohdaten = json.loads(NOTEBOOK_EXPORT_PFAD.read_text(encoding="utf-8"))
    return rohdaten["rohdaten_fuer_backtest"]["marktscan_alle_kandidaten"]


def _gruppiere_in_scan_laeufe(kandidaten: list[dict]) -> list[list[dict]]:
    rows = sorted(kandidaten, key=lambda r: r["discovered_at"])
    laeufe: list[list[dict]] = []
    aktueller_lauf: list[dict] = []
    letzter_zeitpunkt = None
    for row in rows:
        zeitpunkt = datetime.fromisoformat(row["discovered_at"])
        if (
            letzter_zeitpunkt is not None
            and (zeitpunkt - letzter_zeitpunkt).total_seconds() / 60 > RUN_GAP_MINUTEN
        ):
            laeufe.append(aktueller_lauf)
            aktueller_lauf = []
        aktueller_lauf.append(row)
        letzter_zeitpunkt = zeitpunkt
    if aktueller_lauf:
        laeufe.append(aktueller_lauf)
    return laeufe


def _ueberlebende_sortiert_nach_score(lauf: list[dict]) -> list[dict]:
    """Stufe-A-Ueberlebende (score_gesamt gesetzt), absteigend nach Score -
    fuer den Top-N-Deckel muessen die SCHWAECHSTEN zuerst wegfallen."""
    ueberlebende = [r for r in lauf if r["score_gesamt"] is not None]
    return sorted(ueberlebende, key=lambda r: r["score_gesamt"], reverse=True)


def _kosten_je_lauf(lauf: list[dict], top_n: int | None, usd_only: bool) -> int:
    trending_zusatz = sum(
        1 for r in lauf
        if r["discovery_source"] == "trending" and r["score_gesamt"] is None
        # trending-Kandidaten, die AUCH unter score_gesamt landen, wurden
        # ohnehin schon ueber den Stufe-A-Zweig gezaehlt (kein doppelter
        # Zusatz-Call fuer denselben Coin) - _collect_raw_candidates()
        # ueberspringt den get_simple_prices()-Zusatz-Call fuer Trending-
        # Coins, die bereits unter den Top-Gainern sind, siehe dort.
    ) + sum(
        1 for r in lauf if r["discovery_source"] == "trending" and r["score_gesamt"] is not None
    )
    ueberlebende = _ueberlebende_sortiert_nach_score(lauf)
    if top_n is not None:
        ueberlebende = ueberlebende[:top_n]
    backfill_calls_je_kandidat = 1 if usd_only else 2
    return FIXKOSTEN_JE_LAUF + trending_zusatz + len(ueberlebende) * backfill_calls_je_kandidat


def _uebernahmequote(kandidaten: list[dict]) -> dict:
    gesamt = len(kandidaten)
    uebernommen = sum(1 for r in kandidaten if r["status"] == "nutzer_behalten_manuell_uebernommen")
    return {
        "gesamt": gesamt,
        "uebernommen": uebernommen,
        "quote_prozent": round(100 * uebernommen / gesamt, 2) if gesamt else 0.0,
    }


def main() -> None:
    kandidaten = _lade_kandidaten()
    laeufe = _gruppiere_in_scan_laeufe(kandidaten)

    print(f"Geladen: {len(kandidaten)} Kandidaten, gruppiert in {len(laeufe)} Scan-Laeufe "
          f"(Zeitraum {laeufe[0][0]['discovered_at'][:10]} bis {laeufe[-1][-1]['discovered_at'][:10]})")

    baseline_gesamt = 0
    usd_only_gesamt = 0
    top_n_gesamt = {n: 0 for n in TOP_N_VARIANTEN}
    ueberlebende_je_lauf = []

    for lauf in laeufe:
        baseline_gesamt += _kosten_je_lauf(lauf, top_n=None, usd_only=False)
        usd_only_gesamt += _kosten_je_lauf(lauf, top_n=None, usd_only=True)
        for n in TOP_N_VARIANTEN:
            top_n_gesamt[n] += _kosten_je_lauf(lauf, top_n=n, usd_only=True)
        ueberlebende_je_lauf.append(len(_ueberlebende_sortiert_nach_score(lauf)))

    anzahl_laeufe = len(laeufe)
    print(f"\nStufe-A-Ueberlebende je Lauf: min={min(ueberlebende_je_lauf)}, "
          f"max={max(ueberlebende_je_lauf)}, "
          f"durchschnitt={sum(ueberlebende_je_lauf)/anzahl_laeufe:.1f}")

    print(f"\nGesamtkosten ueber {anzahl_laeufe} Laeufe (ATH-Abstand-Calls fuer junge "
          f"Kandidaten NICHT enthalten - Alter wird nicht dauerhaft gespeichert, siehe "
          f"Modul-Docstring):")
    print(f"  Baseline (aktuell, USD+EUR, kein Deckel):  {baseline_gesamt:5d} Calls "
          f"({baseline_gesamt/anzahl_laeufe:.1f}/Lauf, {2*baseline_gesamt/anzahl_laeufe:.1f}/Tag bei 2 Laeufen/Tag)")
    print(f"  USD-only, kein Deckel:                     {usd_only_gesamt:5d} Calls "
          f"({usd_only_gesamt/anzahl_laeufe:.1f}/Lauf, {2*usd_only_gesamt/anzahl_laeufe:.1f}/Tag) "
          f"-> Ersparnis {100*(1-usd_only_gesamt/baseline_gesamt):.1f}%")
    for n in TOP_N_VARIANTEN:
        gesamt = top_n_gesamt[n]
        betroffene_laeufe = sum(1 for c in ueberlebende_je_lauf if c > n)
        print(f"  USD-only + Top-{n}-Deckel:                  {gesamt:5d} Calls "
              f"({gesamt/anzahl_laeufe:.1f}/Lauf, {2*gesamt/anzahl_laeufe:.1f}/Tag) "
              f"-> Ersparnis {100*(1-gesamt/baseline_gesamt):.1f}%, "
              f"Deckel griff in {betroffene_laeufe}/{anzahl_laeufe} Laeufen "
              f"({100*betroffene_laeufe/anzahl_laeufe:.1f}%)")

    quote = _uebernahmequote(kandidaten)
    print(f"\nUebernahmequote (Begruendung fuer USD-only): {quote['uebernommen']}/{quote['gesamt']} "
          f"({quote['quote_prozent']}%) aller je entdeckten Marktscan-Kandidaten wurden je in die "
          f"echte Watchlist uebernommen.")

    print(f"\nEinordnung: der dokumentierte Fixboden (refresh_prices+refresh_history+"
          f"marktscan_backward_tracking) liegt bei ~223 Calls/Tag (siehe Memory "
          f"project_coingecko_kontingent_tracking.md). Baseline-Marktscan-Anteil oben "
          f"({2*baseline_gesamt/anzahl_laeufe:.0f}/Tag) plus Fixboden ergibt "
          f"~{223 + 2*baseline_gesamt/anzahl_laeufe:.0f}/Tag rein aus diesen beiden Quellen "
          f"(JIT-Refresh aus echten Signal-Ereignissen kommt zusaetzlich dazu, hier nicht "
          f"mitgerechnet).")


if __name__ == "__main__":
    main()
