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

    # C6 DIE ROLLEN-KETTE - seit dem Umbau der wichtigste Messpunkt (13.08.).
    #
    # Die Zeilen darueber messen AUFGELOESTE Signale. Die Kette misst, ob
    # ueberhaupt eines entsteht - und das war fast zwei Wochen lang die
    # eigentliche Frage: 98,2 % HALTEN heisst n=0 fuer alles darunter.
    rk = d.get("rollen_kette") or {}
    laeufe = (rk.get("gate_durchlaessigkeit") or {}).get("laeufe") or []
    if not laeufe:
        print("      Rollen-Kette: keine Laeufe im Export "
              "(Datei aelter als der Umbau, oder die Kette lief nicht)")
    for lauf in laeufe[:5]:
        best = lauf.get("bestanden") or {}
        fz = lauf.get("faktorzahlen")
        print(f"      {str(lauf.get('erfasst_am'))[:16]} "
              f"{lauf.get('hinein'):>3} hinein | Urteil {best.get('urteil', 0):>3} "
              f"| Einstieg {best.get('aktion', 0):>3} "
              f"| gerechnet {best.get('risikoschicht', 0):>3} "
              f"| traegt sich {best.get('entscheider', 0):>3}"
              + (f" | Faktorzahl {sorted(set(fz))}" if isinstance(fz, list) and fz else ""))

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

    # D6 KOMMEN DIE FELDER DER NEUEN KETTE MIT?
    #
    # GENAU DIE FALLE, DIE DIESER ABSCHNITT MEINT. Bis zum 13.08. exportierte
    # `extract_notebook_diagnose.py` 18 Tabellen und vom gesamten LLM-Umbau
    # keine einzige. Jede Auswertung waere auf den Altdaten gelaufen und haette
    # die Schluesse der ALTEN Kette bestaetigt - ohne dass irgendwo ein Fehler
    # gemeldet worden waere. Ein fehlendes Feld sieht aus wie ein leeres.
    # DIE NAMEN STAMMEN AUS `agent/signal_abbildung.py`, NICHT AUS DEM PLAN.
    # Der erste Wurf listete `rolle_begruendung` - so heisst die Spalte im
    # Umbauplan Kap. 14.2, aber nirgends im Code. Die Pruefung meldete daher
    # eine Luecke, die es nicht gibt. Immer an der Quelle nachsehen; ein Plan
    # ist eine Absicht, keine Festlegung.
    neu = ("quelle_kette", "lagebild_id", "prompt_stand",
           "unabhaengige_faktoren", "umgeworfen_durch",
           "umgeworfen_preis_eur", "umgeworfen_bis",
           "schwankung_perzentil", "momentum_perzentil",
           "volumen_perzentil", "zai_stimmen", "richtung", "hebel",
           "modell")
    beispiel = (ss or hs or [{}])[0]
    fehlend = [f for f in neu if f not in beispiel]
    zeile(not fehlend,
          f"D6  Felder der Rollen-Kette in den Signalzeilen: "
          f"{'alle ' + str(len(neu)) + ' da' if not fehlend else 'FEHLEN: ' + ', '.join(fehlend)}",
          warnung=bool(fehlend))
    zeile("rollen_kette" in d,
          "D7  Block 'rollen_kette' im Export (Lagebilder + Durchlaessigkeit)",
          warnung="rollen_kette" not in d)
    # Ein Signal der neuen Kette ohne `lagebild_id` ist eine stumme Zeile: das
    # Urteil stuende da, die Marktlage dazu waere nicht mehr auffindbar.
    # (Nach `facts_json` wird hier NICHT gefragt - das ist im Export bewusst
    # ausgeschlossen, siehe Kopf von extract_notebook_diagnose.)
    aus_kette = [s for s in (ss + hs) if s.get("quelle_kette") == "rollen"]
    if aus_kette:
        ohne = [s for s in aus_kette if not s.get("lagebild_id")]
        zeile(not ohne,
              f"D8  Signale aus der neuen Kette: {len(aus_kette)}, davon "
              f"{len(ohne)} ohne lagebild_id",
              warnung=bool(ohne))
    else:
        print(f"{JA}D8  noch kein Signal mit quelle_kette='rollen' "
              f"({len(ss) + len(hs)} Altsignale) - erwartet vor dem Scharfgang")

    # ------------------------------------------------------------ E
    #
    # ⚠️ NEU MIT DEM ROLLOUT VON PAKET B (12.09.2026). Ohne diesen Block
    # prueft der Vollcheck den Stand von gestern: der Hebel kommt seit
    # heute aus der WAHRSCHEINLICHKEIT, alle Hebelrisiken zusammen sind
    # gedeckelt, und die Akkumulation ist gesperrt. Nichts davon war
    # vorher im Export - und was nicht exportiert wird, wird nicht
    # geprueft.
    kopf("E) PAKET B - kommt der Hebel aus der Wahrscheinlichkeit?")
    pb = d.get("paket_b") or {}
    if not pb or pb.get("nicht_verfuegbar"):
        print(NEIN + "E   kein Paket-B-Abschnitt im Export - die Datei ist "
              "von vor dem 12.09., oder der Abschnitt ist ausgefallen: %s"
              % (pb.get("nicht_verfuegbar") or "fehlt"))
    else:
        sch = pb.get("schalter") or {}
        hq = sch.get("hebel_aus_quote") or {}

        def _z(wert, soll):
            """Zahlenvergleich, der eine fehlende Zahl NICHT als gleich liest."""
            try:
                return abs(float(wert) - soll) < 1e-9
            except (TypeError, ValueError):
                return False

        zeile(bool(hq.get("aktiv")),
              f"E1a der Hebel aus der Quote ist SCHARF (aktiv={hq.get('aktiv')}, "
              f"Quelle {(sch.get('quelle') or {}).get('aktiv', '?')})",
              warnung=True)
        zeile(_z(hq.get("aggregat_anteil"), 0.03) and _z(hq.get("hebel_grenze"), 5.0)
              and _z(hq.get("hebel_ab"), 2.0) and _z(hq.get("hebelnenner_eur"), 500.0),
              f"E1b die Regeln stehen wie entschieden: Deckel "
              f"{hq.get('aggregat_anteil')} · Grenze {hq.get('hebel_grenze')}x · "
              f"ab {hq.get('hebel_ab')}x · Nenner {hq.get('hebelnenner_eur')} EUR",
              warnung=True)
        # ⚠️ Der alte Marktscan bleibt AN (Nutzerentscheidung 12.09., 2.385):
        # er ist die einzige Entdeckung ausserhalb der Watchlist. Deshalb
        # hier eine ANZEIGE, keine Forderung.
        zeile(not sch.get("hebel_screening_aktiv"),
              "E1c das ALTE Hebel-Screening ist aus (Positionsabgleich und "
              "Hebelfuehrung laufen weiter)", warnung=True)
        print(JA + f"E1d alter Marktscan: "
              f"{'an' if sch.get('marktscan_aktiv') else 'aus'} - entschieden am 12.09., der Ersatz wird erst gemessen (Schritt 39)")

        kap = pb.get("kapital") or {}
        zeile(bool(kap.get("verwendbar")) and kap.get("zustand") == "frisch",
              f"E2a das Kapital ist verwendbar und frisch: "
              f"{kap.get('wert_eur')} EUR, Stand {kap.get('datum')} "
              f"({kap.get('zustand')})", warnung=True)
        # ⚠️ 2.387-job: der Schreibjob stand zehn Tage. Das Nachrechnen hat
        # die Luecke geschlossen, nicht die Ursache - deshalb hier die
        # Frage, ob er WIEDER taeglich schreibt.
        zeile((kap.get("alter_tage") if kap.get("alter_tage") is not None
               else 99) <= 1,
              f"E2b der Portfoliowert-Job schreibt wieder taeglich "
              f"(juengste Zeile {kap.get('datum')}, {kap.get('alter_tage')} "
              f"Tage alt) - 2.387-job", warnung=True)

        agg = pb.get("aggregat_deckel") or {}
        if agg.get("deckel_eur") is not None:
            soll = float(agg.get("anteil") or 0) * float(agg.get("kapital_eur") or 0)
            zeile(abs(float(agg["deckel_eur"]) - soll) < 0.01
                  and float(agg.get("frei_eur") or 0) >= 0.0,
                  f"E3  {agg.get('satz')}", warnung=True)
        else:
            print(WARN + f"E3  kein Deckel rechenbar: "
                  f"{agg.get('nicht_rechenbar') or agg.get('nicht_ermittelbar')}")

        # ⚠️⚠️ DIE NAHT, AN DER H-5 HING: bis zum 11.09. schrieb die Kette
        # das Instrument NIE (0 von 3.859 Zeilen), und der Aggregat-Deckel
        # haette seine eigenen Signale nicht wiedergefunden.
        sz = pb.get("signalzeilen") or {}
        if "je_instrument" in sz:
            print(JA + f"E4a Signalzeilen je Instrument: {sz['je_instrument']}")
            zeile(sz.get("hebelzeilen_ohne_verlust") == 0
                  and sz.get("hebelzeilen_unter_2x") == 0,
                  f"E4b jede Hebelzeile traegt ihren Verlust am Stop und "
                  f"Hebel >= 2x (ohne Verlust {sz.get('hebelzeilen_ohne_verlust')}, "
                  f"unter 2x {sz.get('hebelzeilen_unter_2x')})", warnung=True)
            zeile(sz.get("akkumulationssignale") == 0,
                  f"E5  keine Akkumulationssignale - gesperrt bis Paket 2 "
                  f"({sz.get('akkumulationssignale')} Zeilen)", warnung=True)
        else:
            print(WARN + f"E4  Signalzeilen nicht auswertbar: {sz}")

        fue = pb.get("hebelfuehrung")
        if isinstance(fue, list):
            ohne_plan = [x for x in fue if not x.get("plan_signal_id")]
            senken = [x for x in fue if x.get("liquidation_vor_stop")]
            print(JA + f"E6a {len(fue)} offene Hebelposition(en), davon "
                  f"{len(ohne_plan)} ohne zugeordnetes Signal (zaehlen mit "
                  f"11,7 % im Deckel) und {len(senken)} mit Liquidation vor "
                  f"dem Stop")
            zeile(all(x.get("nachschuss_eur") is not None for x in senken),
                  "E6b jede Position mit Liquidation vor dem Stop nennt ihren "
                  "Nachschuss", warnung=True)
        else:
            print(WARN + f"E6  Hebelfuehrung nicht lesbar: {fue}")

        # Die Einmal-Marken sind der BELEG, dass die Fuehrung gemeldet hat -
        # sie stehen in `job_laeufe`, sind aber keine Jobs (H-4).
        marken = ((d.get("joblaeufe") or {}).get("einmal_marken") or {})
        print(JA + f"E7  Meldungen der Hebelfuehrung bisher: "
              f"{marken.get('anzahl', 0)}"
              + (f" · juengste: {marken.get('juengste')[:3]}"
                 if marken.get("juengste") else ""))
    print()
    print("=" * 92)
    print(f"OFFENE PUNKTE: {len(befunde)}")
    for b in befunde:
        print(f"  - {b}")


if __name__ == "__main__":
    main()
