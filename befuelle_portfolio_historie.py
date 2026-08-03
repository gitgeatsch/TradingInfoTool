"""Portfolio-Wert-Historie rueckwirkend befuellen (Task #612, Z-3/RM-7).

AM NOTEBOOK AUSFUEHREN, nach `git pull`:
    python befuelle_portfolio_historie.py            # Probelauf, schreibt NICHTS
    python befuelle_portfolio_historie.py --schreiben # schreibt in die Datenbank

WARUM ES DAS BRAUCHT
Ohne diesen Lauf beginnt die Wertreihe erst beim naechsten
portfolio_wert_job() - Z-3 waere dann wochenlang ohne Aussagekraft (pruefe_z3()
meldet das immerhin selbst als `datenbasis_duenn`). Mit dem Lauf stehen
rueckwirkend rund 88 Tage zur Verfuegung, begrenzt durch die Kurshistorie, nicht
durch die Transaktionen (die reichen bis 09/2024).

PROBELAUF IST DER STANDARD, mit Absicht: der Lauf schreibt in eine Tabelle, auf
die spaeter eine harte Regel zugreift. Erst ansehen, was herauskommt, dann
schreiben. `--schreiben` ist eine bewusste zweite Entscheidung.

WORAUF BEIM PROBELAUF ZU ACHTEN IST - der Ausdruck zeigt es:
  * "Ohne Verlauf" MUSS 0 sein. Steht dort etwas, fehlen dem Export die
    `/trades` (alte Fassung des Export-Skripts) - dann liefen Aktien/ETF/ETC
    mit konstanter Menge, und der Hoechststand, gegen den Z-3 spaeter misst,
    entstuende auf Naeherungsdaten.
  * Bestandsabgleich: der rekonstruierte Ist-Bestand MUSS holdings.quantity
    treffen. Stimmt er nicht, ist auch jeder historische Tageswert falsch.
    Einzige bekannte Ausnahme zum Stand 04.08.: SPC (eine reward-Gutschrift von
    6,29 Einheiten, die `holdings` ueberhaupt nicht fuehrt).
  * Symbole ohne Kurs je Tag: steigt die Zahl, fehlen Kurse und der Tageswert
    ist zu niedrig - das saehe aus wie ein Kursrutsch.
  * Der Indexverlauf selbst: er bildet Marktbewegung ab, KEINE Zu-/Verkaeufe.
    Ein Sprung an einem Tag, an dem du gehandelt hast, waere ein Warnsignal.

Nur lesend, ausser mit --schreiben. Kein Netzwerk-Call: Transaktionen kommen
aus dem Export, Kurse aus der lokalen Datenbank.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import database.db as db
from agent.portfolio_historie import (
    QUELLE_REKONSTRUIERT,
    bestandsverlauf,
    groesster_rueckschlag,
    pruefe_gegen_holdings,
    rekonstruiere_aus_transaktionen,
    reihen_je_kategorie,
)
from api.bitpanda import BITPANDA_SYMBOL_OVERRIDES
from extract_notebook_diagnose import ZIEL_ORDNER

EXPORT = ZIEL_ORDNER / "bitpanda_transaktionen.json"

# Die Kurshistorie beginnt einheitlich am 2026-05-08 (gemessen 04.08.). Frueher
# anzusetzen erzeugt nur Tage ohne Kurse; wer die Reihe spaeter verlaengert,
# aendert diesen Wert.
AB_DATUM = "2026-05-08"


def main() -> None:
    schreiben = "--schreiben" in sys.argv
    print("Portfolio-Wert-Historie befuellen (Task #612)")
    print("MODUS:", "SCHREIBEN" if schreiben else "PROBELAUF (schreibt nichts)")
    print()

    if not EXPORT.exists():
        raise SystemExit(
            f"Export nicht gefunden: {EXPORT}\n"
            "Zuerst `python extract_bitpanda_transaktionen.py` laufen lassen."
        )
    daten = json.load(io.open(EXPORT, encoding="utf-8"))
    transaktionen = daten["transaktionen"]
    # Seit 04.08. im Export: Trades aller Assetklassen (Task #613). Ohne sie
    # laufen Aktien/ETF/ETC mit konstanter Menge - siehe bestandsverlauf().
    trades = daten.get("trades") or []
    holdings_export = {h["symbol"]: h["quantity"] for h in daten["holdings_schnappschuss"]}
    print(f"Export vom {daten['erzeugt_am'][:10]}: {len(transaktionen)} Transaktionen, "
          f"{len(trades)} Trades, {len(holdings_export)} Bestandszeilen")
    if not trades:
        print("  ACHTUNG: keine Trades im Export - Aktien/ETF/ETC laufen dann mit")
        print("  konstanter Menge. Fuer eine saubere Reihe zuerst")
        print("  `python extract_bitpanda_transaktionen.py` in der aktuellen Fassung laufen lassen.")

    overrides = {v: k for k, v in BITPANDA_SYMBOL_OVERRIDES.items()}
    watchlist = config.get_watchlist()
    conn = db.get_connection()
    try:
        # --- Schritt 1: Pruefstein ------------------------------------------
        # Vorwaerts von null ueber die volle Historie. Rueckwaerts vom heutigen
        # Bestand waere der Abgleich per Konstruktion erfuellt und wuerde jede
        # falsche Regel bestehen.
        print("\n--- Bestandsabgleich (der Pruefstein) ---")
        verlauf = bestandsverlauf(transaktionen, symbol_overrides=overrides, trades=trades)
        pruefung = pruefe_gegen_holdings(verlauf, holdings_export)
        print(f"  Treffer:            {len(pruefung['treffer'])}")
        print(f"  Glatt aufgeloest:   {len(pruefung['glatt_aufgeloest'])}")
        print(f"  Ohne Verlauf:       {len(pruefung['nicht_im_verlauf'])} "
              f"-> {pruefung['nicht_im_verlauf']}")
        print(f"  ABWEICHUNGEN:       {len(pruefung['abweichungen'])}")
        for symbol, soll, ist in pruefung["abweichungen"]:
            print(f"     {symbol}: holdings={soll:.6f} rekonstruiert={ist:.6f}")
        if len(pruefung["abweichungen"]) > 1:
            print("\n  ACHTUNG: mehr als die eine bekannte Bagatelle (SPC). Das deutet auf")
            print("  eine Buchungsart hin, die die Regel nicht kennt - z. B. einen neuen")
            print("  Bitpanda-Tag. NICHT schreiben, bevor das geklaert ist.")

        # --- Schritt 2: Wertreihe -------------------------------------------
        print(f"\n--- Wertreihe ab {AB_DATUM} ---")
        reihe, diagnose = rekonstruiere_aus_transaktionen(
            conn, transaktionen, holdings_export,
            ab_datum=AB_DATUM, watchlist=watchlist, symbol_overrides=overrides,
            trades=trades,
        )
        if not reihe:
            raise SystemExit("Keine Tage mit Kursen gefunden - Kurshistorie pruefen.")
        print(f"  {len(reihe)} Tage: {reihe[0][0]} bis {reihe[-1][0]}")
        print(f"  Naeherung konstante Menge: {diagnose['naeherung_konstante_menge']}")
        if diagnose["ohne_jeden_kurs"]:
            print(f"  OHNE JEDEN KURS: {diagnose['ohne_jeden_kurs']}")
        maximal_ohne_kurs = max(z[3] for z in reihe)
        print(f"  Symbole ohne Kurs, schlimmster Tag: {maximal_ohne_kurs}")

        print("\n  Erste und letzte fuenf Tage:")
        for datum, wert, index, ohne in reihe[:5] + reihe[-5:]:
            print(f"     {datum}  wert={wert:12.2f} EUR  index={index:8.3f}  ohne_kurs={ohne}")

        # --- Schritt 3: Rueckschlag je Kategorie ----------------------------
        print("\n--- Rueckschlag (Z-3 rechnet auf 'gesamt') ---")
        schwelle = config.load_config().get("ziele", {}).get("max_drawdown_prozent", 15)
        for name, (kat_reihe, kat_diag) in reihen_je_kategorie(
            conn, transaktionen, holdings_export,
            ab_datum=AB_DATUM, watchlist=watchlist, symbol_overrides=overrides,
            trades=trades,
        ).items():
            if not kat_reihe:
                continue
            d = groesster_rueckschlag([(t, i, 0) for t, _, i, _ in kat_reihe])
            marke = "  <-- Z-3" if name == "gesamt" else ""
            naeh = "" if not kat_diag["naeherung_konstante_menge"] else " (mit Naeherung)"
            print(f"  {name:12s} max {d['max_prozent']:6.2f}%  aktuell {d['aktuell_prozent']:6.2f}%"
                  f"  Schwelle {schwelle}%{marke}{naeh}")

        # --- Schritt 4: schreiben -------------------------------------------
        if not schreiben:
            print("\nPROBELAUF beendet - es wurde nichts geschrieben.")
            print("Wenn die Zahlen oben plausibel sind:")
            print("    python befuelle_portfolio_historie.py --schreiben")
            return

        print(f"\n--- Schreiben ({QUELLE_REKONSTRUIERT}) ---")
        gesamt_verlauf = bestandsverlauf(transaktionen, symbol_overrides=overrides, trades=trades)
        bewegungstage = sorted(gesamt_verlauf)
        konstant = {
            s: m for s, m in holdings_export.items()
            if m > 0 and (not bewegungstage or s not in gesamt_verlauf[bewegungstage[-1]])
        }
        for datum, wert, index, ohne_kurs in reihe:
            stand: dict = {}
            for tag in bewegungstage:
                if tag > datum:
                    break
                stand = gesamt_verlauf[tag]
            db.upsert_portfolio_wert(
                conn, datum, wert,
                cash_eur=0.0,  # historisch nicht rekonstruierbar, siehe Modul-Docstring
                symbole_gesamt=len(stand) + len(konstant),
                symbole_ohne_kurs=ohne_kurs,
                quelle=QUELLE_REKONSTRUIERT,
                index_wert=index,
                mengen_json=json.dumps({**stand, **konstant}),
                commit=False,
            )
        conn.commit()
        print(f"  {len(reihe)} Tage geschrieben.")
        print("\nDer taegliche Job (6:30) setzt die Reihe ab morgen mit quelle='laufend'")
        print("fort und ueberschreibt rekonstruierte Tage nicht rueckwirkend.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
