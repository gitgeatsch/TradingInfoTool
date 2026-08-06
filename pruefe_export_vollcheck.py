"""Vollcheck des Notebook-Exports (2026-08-06).

WOFUER. `pruefe_export_standard.py` geht den festen 15-Punkte-Katalog durch -
das ist die Routine. Dieses Skript beantwortet die vier Fragen, die nach einer
Phase mit vielen Aenderungen dazukommen und die der Katalog NICHT abdeckt:

  A) Wirken die Fixes der letzten Tage im Betrieb - jeder einzeln nachgewiesen?
  B) Laufen Backward-Tracking, Schatten-Messung und Monitoring sauber, oder
     haengt etwas still?
  C) Wo steht jeder Messpunkt der Messkette - gemessen, offen, blockiert?
  D) Fehlen relevante Informationen, die eine spaetere Auswertung kippen wuerden?

Der Unterschied zum Katalog ist die Blickrichtung: der Katalog fragt "sind die
Kennzahlen auffaellig", dieses Skript fragt "stimmt das, was wir glauben
gebaut zu haben". Beides ist noetig - der Nur-Long-Umbau haette in jedem
Kennzahlen-Katalog unauffaellig ausgesehen, weil er die Kennzahlen gar nicht
beruehrt.

Liest ausschliesslich den Export, keine Produktiv-DB.
"""
from __future__ import annotations

import collections
import io
import json
import sys
from datetime import datetime, timedelta, timezone

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')

JA, NEIN, WARN = "  [ok] ", "  [--] ", "  [!!] "
befunde: list[str] = []


def zeile(gut: bool, text: str, warnung: bool = False) -> None:
    if gut:
        print(JA + text)
    else:
        print((WARN if warnung else NEIN) + text)
        if warnung:
            befunde.append(text)


def kopf(t: str) -> None:
    print()
    print("=" * 92)
    print(t)
    print("=" * 92)


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    d = json.load(io.open(pfad, encoding="utf-8"))
    hs = d.get("hebel_signals", [])
    ss = d.get("spot_signals", [])
    lg = [l for l in d.get("log_auszug", []) if isinstance(l, str)]
    heute = max((s.get("created_at") or "")[:10] for s in hs)

    # ------------------------------------------------------------ A
    kopf("A) WIRKEN DIE FIXES? - jeder einzeln am Betrieb nachgewiesen")

    # A1 Nur-Long-Umbau
    nl = [s for s in hs if "Nur Long" in (s.get("risk_veto_reason") or "")]
    letztes_nl = max((s["created_at"] for s in nl), default="-")[:16]
    zeile(letztes_nl < "2026-08-05T18",
          f"A1a Nur-Long-Veto feuert nicht mehr (letztes: {letztes_nl})", warnung=True)
    short_eroeffnen = [s for s in hs if (s.get("created_at") or "")[:10] == heute
                       and s.get("richtung") == "SHORT" and s.get("action") == "ERÖFFNEN"]
    zeile(bool(short_eroeffnen),
          f"A1b SHORT erreicht den regulaeren Pfad: {len(short_eroeffnen)} SHORT-EROEFFNEN heute")
    unterdrueckt = [l for l in lg if "unterdrueckt" in l and "nur_long" in l and heute in l]
    zeile(len(unterdrueckt) == len(short_eroeffnen) or not short_eroeffnen,
          f"A1c E-Mail-Filter griff {len(unterdrueckt)}x bei {len(short_eroeffnen)} SHORT-EROEFFNEN")

    # A2 Ausstiegsregel
    ae = (d.get("ausstiegs_empfehlungen") or {}).get("empfehlungen") or []
    job_da = any("ausstiegs_job" in l for l in lg)
    gelaufen = [l for l in lg if "ausstiegs_job" in l and "Running job" in l]
    zeile(job_da, "A2a Ausstiegs-Job ist registriert")
    zeile(bool(gelaufen), f"A2b Ausstiegs-Job ist gelaufen ({len(gelaufen)}x im Log-Fenster)",
          warnung=True)
    zeile(bool(ae), f"A2c Empfehlungen vorhanden: {len(ae)}, "
                    f"{sum(x.get('sichert_r') or 0 for x in ae):.1f} R ungesichert")

    # A3 Neue Fakten
    fk = d.get("hebel_faktensaetze") or {}
    bjt = fk.get("bloecke_je_tag") or {}
    heutige = bjt.get(heute, {})
    n_saetze = heutige.get("_faktensaetze", 0)
    for name in ("kosten", "ausstiegsregel", "systemguete", "crv_baender"):
        n = heutige.get(name, 0)
        zeile(n > 0 and n == n_saetze,
              f"A3  Fakt '{name}': {n} von {n_saetze} Faktensaetzen heute")
    # A4 Export-Werkzeuge (VOR A3b, weil A3b davon abhaengt)
    zeile("fenster_tage" in fk, f"A4a Faktensatz-Fenster rolliert ({fk.get('fenster_tage')} Tage)")
    zeile(bool(bjt), "A4b bloecke_je_tag vorhanden")
    zweistufig = any("." in k for k in heutige)
    zeile(zweistufig, "A4c Zaehler erfasst verschachtelte Schluessel (eltern.kind)")

    # A3b score_gesamt - NUR pruefbar, wenn der Zaehler zwei Ebenen erfasst.
    #
    # DIESE ABHAENGIGKEIT IST DER GRUND FUER DEN BLOCK. Der erste Wurf dieses
    # Skripts meldete "score_gesamt entfernt: 0 von 22" als gruenen Haken - und
    # das war ein FALSCHES GRUEN: der Zaehler im Export war die alte Fassung,
    # die verschachtelte Schluessel gar nicht sieht. Eine Null bedeutet dort
    # "nicht gezaehlt", nicht "nicht vorhanden". Ein Pruefskript, das einen
    # blinden Fleck als Bestaetigung ausgibt, ist schlimmer als keines.
    if not zweistufig:
        print(NEIN + "A3b score_gesamt: NICHT PRUEFBAR - der Zaehler in diesem Export "
                     "sieht keine verschachtelten Schluessel (0 waere hier kein Beleg)")
    else:
        sg = heutige.get("trigger.score_gesamt", 0)
        zeile(sg == 0, f"A3b score_gesamt entfernt (noch in {sg} von {n_saetze})")

    # A5 Entfernte Provider - im EXPORT gehoeren die Altdaten hin.
    # Bewusste Entscheidung vom 05.08.: gefiltert wird NUR die Anzeige auf der
    # Remote-Seite, Daten und Export bleiben vollstaendig. Historische
    # Cerebras-Signale sind korrekte Historie, kein Altlast-Fehler - sie hier
    # zu vermissen waere die falsche Erwartung.
    pp = d.get("provider_performance", {})
    hist = [t for t, v in pp.items() if isinstance(v, dict) and "cerebras" in v]
    print(f"{JA}A5  Cerebras nur noch als Historie im Export ({len(hist)} Tiers) - "
          f"so gewollt, die Remote-Seite filtert nur die Anzeige")

    # ------------------------------------------------------------ B
    kopf("B) LAUFEN BACKTRACKING, SCHATTEN-MESSUNG UND MONITORING?")

    def frisch(feld, quelle, label):
        werte = [s.get(feld) for s in quelle if s.get(feld)]
        neuestes = max(werte)[:16] if werte else "-"
        alt = neuestes[:10] < heute
        zeile(not alt, f"{label}: zuletzt {neuestes} ({len(werte)} Eintraege)", warnung=alt)

    frisch("outcome_geprueft_am", hs, "B1  Hebel-Backward-Tracking")
    frisch("outcome_geprueft_am", ss, "B2  Spot-Backward-Tracking")
    frisch("veto_outcome_geprueft_am", hs, "B3  Veto-Schatten-Tracking")
    frisch("selbst_halten_outcome_geprueft_am", hs, "B4  Selbst-HALTEN-Tracking")

    sg_block = d.get("systemguete") or {}
    gefuellt = [t for t, v in sg_block.items()
                if isinstance(v, dict) and (v.get("real") or {}).get("anzahl_bewertet")]
    zeile(len(gefuellt) >= 2, f"B5  Systemguete berechnet fuer: {gefuellt}")

    # Haengende Signale: alt genug, aber ohne jeden Outcome
    grenze = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
    haengend = [s for s in hs
                if (s.get("created_at") or "") < grenze
                and not s.get("outcome_status")
                and not s.get("veto_outcome_status")
                and not s.get("selbst_halten_outcome_status")]
    zeile(len(haengend) < 20,
          f"B6  Signale aelter als 21 Tage ganz ohne Outcome: {len(haengend)}",
          warnung=len(haengend) >= 20)

    zai = d.get("zai_gegenpruefung_verlauf") or {}
    zeile(bool(zai.get("anzahl_gesamt")),
          f"B7  Z.ai-Gegenpruefung: {zai.get('anzahl_gesamt')} Signale mit Urteil "
          f"({zai.get('anzahl_widerspruch')} Widerspruch)")

    # ------------------------------------------------------------ C
    kopf("C) STATUS DER MESSPUNKTE")
    hebel_real = ((d.get("systemguete") or {}).get("hebel") or {}).get("real") or {}
    krypto_real = ((d.get("systemguete") or {}).get("krypto") or {}).get("real") or {}
    print(f"      Hebel  n={hebel_real.get('anzahl_bewertet')}  EW {hebel_real.get('expectancy_r')}  "
          f"SQN {hebel_real.get('sqn')}  Signalbeitrag {hebel_real.get('signalbeitrag_r')}")
    print(f"      Krypto n={krypto_real.get('anzahl_bewertet')}  EW {krypto_real.get('expectancy_r')}")
    baender = d.get("crv_breakeven_baender") or {}
    belastbar = {k: sum(1 for b in (v or {}).get("baender") or [] if b.get("belastbar"))
                 for k, v in baender.items() if k.endswith("_h7_ohne_halten")}
    print(f"      CRV-Baender mit belastbarem Befund je Tier: {belastbar}")
    rv = d.get("richtungsverteilung") or {}
    print(f"      Richtungsverteilung seit {rv.get('ab_datum')}: "
          f"SHORT-Anteil {rv.get('short_anteil_pct')} %")

    # ------------------------------------------------------------ D
    kopf("D) FEHLENDE INFORMATIONEN, die eine Auswertung kippen wuerden")
    psy = d.get("preishistorie_signal_symbole") or {}
    ohne = psy.get("symbole_ohne_ohlc") or []
    zeile(not ohne, f"D1  Symbole ohne OHLC: {ohne or 'keine'}", warnung=bool(ohne))
    hc = d.get("holdings_check") or []
    ohne_kurs = [h for h in hc if isinstance(h, dict) and h.get("quantity")
                 and not h.get("avg_buy_price_eur") and not h.get("avg_buy_price_manual_eur")]
    zeile(len(ohne_kurs) < 10, f"D2  Positionen ohne Einstandspreis: {len(ohne_kurs)}",
          warnung=len(ohne_kurs) >= 10)
    ws = d.get("watchlist_stammdaten") or {}
    ohne_gruppe = sum(1 for v in ws.values() if not v.get("hauptgruppe"))
    zeile(True, f"D3  Watchlist ohne Hauptgruppe: {ohne_gruppe} von {len(ws)} "
                f"(betrifft nur Klumpen-Auswertungen)")
    mh = (d.get("rohdaten_fuer_backtest") or {}).get("macro_historie") or []
    zeile(len(mh) >= 30, f"D4  Makro-Historie {len(mh)} Zeilen - begrenzt jedes Mischen mit Kursdaten")
    fx = sum(1 for l in lg if "Spannweite" in l)
    zeile(fx == 0, f"D5  Verworfene FX-Ableitungen im Log: {fx}", warnung=fx > 0)

    print()
    print("=" * 92)
    print(f"OFFENE PUNKTE: {len(befunde)}")
    for b in befunde:
        print(f"  - {b}")


if __name__ == "__main__":
    main()
