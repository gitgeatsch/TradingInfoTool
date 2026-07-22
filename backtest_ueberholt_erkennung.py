# -*- coding: utf-8 -*-
"""Backtest (2026-07-22, Nutzer-Vorgabe "das Thema gehen wir gleich an ... "
- siehe Plan-Datei swift-napping-muffin.md, Abschnitt "Ueberholt-Erkennung
reparieren: Mindestbeobachtung + Materialitaets-Check (Hebel+Spot)"): prueft
ALLE historisch als 'ueberholt_durch_neuere_analyse' markierten Hebel-/Spot-
Signale gegen die geplanten zwei neuen Gates, BEVOR irgendein Produktivcode
geaendert wird - gleicher Zwischen-Checkpoint wie beim Budget-Allocator-SLA-
Fix (siehe backtest_budget_allocator_sla.py, Memory
feedback_backtest_first_hard_guarantee.md).

Root Cause (siehe Plan-Datei): `_is_superseded()` (identisch in
agent/krypto/hebel_backward_tracking.py und agent/krypto/backward_tracking.py)
markiert ein noch offenes Signal als ueberholt, sobald IRGENDEINE neuere
Nicht-HALTEN-Aktion fuer denselben Schluessel existiert - unabhaengig vom
Alter und unabhaengig davon, ob die neue These inhaltlich ueberhaupt etwas
anderes sagt. Die zwei geplanten neuen Gates:
- Mindestbeobachtung: ein Signal darf erst nach einer Mindestzeit (abgeleitet
  aus halte_kriterium_bucket, bei Hebel zusaetzlich trade_thesis_typ)
  ueberholt werden.
- Zonen-Reaffirmation: liegen Entry-/Stop-/Take-Profit-Zonen des neuen
  Signals praktisch identisch zum alten, ist das keine neue Information,
  keine Ueberholung.
Bei Spot bleibt eine echte Kurswende (VERKAUFEN/TAUSCHEN nach KAUFEN)
weiterhin SOFORT ueberholend - das war 2026-07-16 der urspruengliche,
korrekte Zweck der Funktion und wird durch die neuen Gates nicht angetastet.

Liest die von extract_notebook_diagnose.py exportierte notebook_diagnose.json
(Sektionen `hebel_signals`/`spot_signals` fuer die Signal-Historie inkl.
Zonen/Zeitstempel + `preishistorie_ueberholte_symbole` fuer die seitherige
echte Kurshistorie, siehe dortiger Modul-Docstring-Nachtrag 2026-07-22).

Ablauf je ueberholtem Signal S:
1. Sammle ALLE spaeteren realen Signale (created_at > S.created_at, action
   != HALTEN) fuer denselben Schluessel (Hebel: symbol+richtung, Spot: nur
   symbol), chronologisch sortiert - das erste davon ist das Signal, dessen
   Erscheinen S unter der HEUTIGEN Regel ueberholt hat (_is_superseded()
   prueft bei jedem taeglichen Lauf gegen die jeweils aktuellste reale
   Signal-Referenz - S wird ueberholt, sobald diese erstmals != HALTEN und
   juenger als S ist).
2. Unter der NEUEN Regel wird die Kette der Reihe nach durchlaufen: fuer
   jeden Kandidaten L pruefen, ob er S TATSAECHLICH ueberholen wuerde - bei
   Spot sofort ja, wenn L eine echte Gegenrichtung ist (VERKAUFEN/TAUSCHEN);
   sonst nur, wenn beide neuen Gates die Ueberholung erlauben
   (Mindestbeobachtung erreicht UND keine Zonen-Reaffirmation). Der erste
   Kandidat, der das erfuellt, wird zum neuen Ausloeser. Erfuellt KEINER der
   Kandidaten das, bleibt S unter der neuen Regel bis zum Ende des
   Exportfensters offen ("gerettet") - das deckt auch den Fall ab, dass die
   erste Ueberholung zu jung ist, eine spaetere in der Kette aber schon
   genuegend Abstand hat.
3. Fuer gerettete Signale: simuliere weiter mit der echten Kurshistorie seit
   S.created_at (price_history_ohlc, EUR - identische Zonen-Waehrung wie im
   Export) bis TP/SL erreicht wird oder der letzte beobachtete Kandidat in
   der Kette erreicht ist (danach waere ohnehin ein neuer Bewertungszyklus
   faellig - die Simulation stoppt dort ehrlich statt unbegrenzt in die
   Zukunft zu schauen), je nachdem was zuerst eintritt. Gleiche Konvention
   wie check_signal_outcome()/check_hebel_signal_outcome(): trifft ein Tag
   beide Zonen, gewinnt Stop-Loss (konservativ, Kapitalerhalt vor Gewinn).

BEWUSSTE VEREINFACHUNG: "real" (siehe database/db.py::
get_latest_real_signal_per_symbol()-Docstring, groq_raw_response IS NOT
NULL) wird hier ueber llm_model/groq_model IS NOT NULL angenaehert - der
schlanke Diagnose-Export enthaelt groq_raw_response bewusst nicht (siehe
extract_notebook_diagnose.py-Modul-Docstring, Spaltenauswahl). Die beiden
neuen Gate-Funktionen sind eine EIGENSTAENDIGE Kopie der geplanten
Produktivlogik (existiert zum Zeitpunkt dieses Backtests noch nicht, siehe
Plan-Datei) - identisches Vorgehen wie backtest_budget_allocator_sla.py.

Aufruf: python backtest_ueberholt_erkennung.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET = {"kurz": 2, "mittel": 5, "lang": 10}
DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK = 3
HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE = 18
ZONEN_REAFFIRMATION_TOLERANZ_RELATIV = 0.03


def _finde_export() -> Path:
    """Gleiches Laufwerksbuchstaben-Problem wie extract_notebook_diagnose.py::
    _google_drive_wurzel() - Desktop/Notebook nutzen unterschiedliche
    Laufwerksbuchstaben fuer Google Drive."""
    for laufwerk in ("K", "G", "H", "E", "F"):
        for ordner in ("My Drive", "Meine Ablage"):
            pfad = Path(f"{laufwerk}:/{ordner}/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json")
            if pfad.exists():
                return pfad
    raise FileNotFoundError(
        "notebook_diagnose.json nicht gefunden - bitte extract_notebook_diagnose.py "
        "am Notebook erneut laufen lassen (nach der Preishistorie-Erweiterung "
        "2026-07-22) und synchronisieren."
    )


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _mid(von, bis) -> float | None:
    if von is not None and bis is not None:
        return (von + bis) / 2
    return von


def _zonen_mittel(signal: dict) -> tuple[float | None, float | None, float | None]:
    entry = _mid(signal.get("entry_eur_von"), signal.get("entry_eur_bis"))
    stop = _mid(signal.get("stop_loss_eur_von"), signal.get("stop_loss_eur_bis"))
    take = _mid(signal.get("take_profit_eur_von"), signal.get("take_profit_eur_bis"))
    return entry, stop, take


def _mindestbeobachtung_stunden(signal: dict, ist_hebel: bool) -> float:
    if ist_hebel and signal.get("trade_thesis_typ") == "einmal_trade":
        return HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE
    bucket = signal.get("halte_kriterium_bucket")
    tage = DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET.get(bucket, DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK)
    return tage * 24.0


def _ist_zonen_reaffirmation(s: dict, l: dict, toleranz_relativ: float) -> bool:
    """Konservativ: fehlt einer der drei Mittelwerte bei einem der beiden
    Signale, gilt das NICHT als Reaffirmation (normale Ueberholung greift,
    kein stiller Sonderfall) - siehe Plan-Datei."""
    paare = list(zip(_zonen_mittel(s), _zonen_mittel(l)))
    if any(a is None or b is None for a, b in paare):
        return False
    return all(abs(a - b) <= toleranz_relativ * abs(a) for a, b in paare if a)


def _ist_real(signal: dict, ist_hebel: bool) -> bool:
    modell_feld = "llm_model" if ist_hebel else "groq_model"
    return bool(signal.get(modell_feld))


def _schluessel(signal: dict, ist_hebel: bool):
    return (signal["symbol"], signal.get("richtung")) if ist_hebel else signal["symbol"]


def _ist_gegenrichtung(action: str | None, ist_hebel: bool) -> bool:
    return (not ist_hebel) and action in ("VERKAUFEN", "TAUSCHEN")


def _chronologische_kandidaten(alle: list[dict], schluessel, nach_zeit: datetime, ist_hebel: bool) -> list[dict]:
    kandidaten = [
        s for s in alle
        if _schluessel(s, ist_hebel) == schluessel
        and _parse(s["created_at"]) > nach_zeit
        and s.get("action") != "HALTEN"
        and _ist_real(s, ist_hebel)
    ]
    return sorted(kandidaten, key=lambda s: s["created_at"])


def _simuliere_weiterverlauf(signal: dict, preisreihe: list[dict], bis: datetime) -> str:
    """Mirrort check_signal_outcome()/check_hebel_signal_outcome(): Stop-Loss
    gewinnt bei Gleichstand am selben Tag (konservativ). Nutzt EUR-Preisreihe
    (currency='EUR'), identische Waehrung wie die exportierten Zonen."""
    entry, stop, take = _zonen_mittel(signal)
    if stop is None or take is None:
        return "nicht_pruefbar"
    start = _parse(signal["created_at"])
    for row in preisreihe:
        if row.get("currency") != "EUR":
            continue
        try:
            row_datum = datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if row_datum < start:
            continue
        if row_datum > bis:
            break
        if row["low"] <= stop:
            return "stop_loss_erreicht"
        if row["high"] >= take:
            return "take_profit_erreicht"
    return "offen_geblieben"


def _naechster_supersede_kandidat(
    kandidaten: list[dict], s: dict, ist_hebel: bool, mindest_stunden: float, toleranz_relativ: float,
) -> tuple[dict | None, str | None]:
    """Durchlaeuft die chronologische Kandidatenkette und gibt den ERSTEN
    zurueck, der S unter der NEUEN Regel tatsaechlich ueberholen wuerde -
    Kandidaten, die keines der Kriterien erfuellen, werden uebersprungen
    (S bleibt bei ihnen offen, die Kette laeuft weiter)."""
    s_zeit = _parse(s["created_at"])
    for l in kandidaten:
        if _ist_gegenrichtung(l.get("action"), ist_hebel):
            return l, "echte_gegenrichtung"
        alter_stunden = (_parse(l["created_at"]) - s_zeit).total_seconds() / 3600
        if alter_stunden < mindest_stunden:
            continue
        if _ist_zonen_reaffirmation(s, l, toleranz_relativ):
            continue
        return l, "materiell_neu"
    return None, None


def _pruefe(alle_signale: list[dict], ist_hebel: bool, preishistorie: dict) -> list[dict]:
    ueberholte = [s for s in alle_signale if s.get("outcome_status") == "ueberholt_durch_neuere_analyse"]
    ergebnisse = []
    for s in ueberholte:
        schluessel = _schluessel(s, ist_hebel)
        s_zeit = _parse(s["created_at"])
        kandidaten = _chronologische_kandidaten(alle_signale, schluessel, s_zeit, ist_hebel)
        if not kandidaten:
            continue  # kein spaeteres reales Signal im Export - Randfall, ueberspringen

        heutiger_ausloeser = kandidaten[0]  # hat S unter der HEUTIGEN (Live-)Regel ueberholt
        mindest_stunden = _mindestbeobachtung_stunden(s, ist_hebel)
        neuer_ausloeser, grund = _naechster_supersede_kandidat(
            kandidaten, s, ist_hebel, mindest_stunden, ZONEN_REAFFIRMATION_TOLERANZ_RELATIV,
        )

        eintrag = {
            "symbol": s["symbol"], "richtung": s.get("richtung"),
            "signal_created_at": s["created_at"],
            "heutiger_ausloeser_created_at": heutiger_ausloeser["created_at"],
            "alter_bei_heutiger_ueberholung_stunden": round(
                (_parse(heutiger_ausloeser["created_at"]) - s_zeit).total_seconds() / 3600, 1,
            ),
            "waere_unter_neuer_regel_ueberholt": neuer_ausloeser is not None,
        }
        if neuer_ausloeser is not None:
            eintrag["neuer_ausloeser_created_at"] = neuer_ausloeser["created_at"]
            eintrag["grund"] = grund
        else:
            eintrag["grund"] = "im_exportfenster_nie_materiell_neu"
            preisreihe = preishistorie.get(s["symbol"], [])
            letzter_kandidat_zeit = _parse(kandidaten[-1]["created_at"])
            eintrag["simuliertes_ergebnis"] = _simuliere_weiterverlauf(s, preisreihe, letzter_kandidat_zeit)
        ergebnisse.append(eintrag)
    return ergebnisse


def main() -> None:
    export_pfad = _finde_export()
    print(f"Lade Export: {export_pfad}")
    with export_pfad.open(encoding="utf-8") as f:
        export = json.load(f)

    preishistorie = export.get("preishistorie_ueberholte_symbole", {}).get("preishistorie_je_symbol", {})

    ergebnisse = {
        "hebel": _pruefe(export.get("hebel_signals", []), True, preishistorie),
        "spot": _pruefe(export.get("spot_signals", []), False, preishistorie),
    }

    for label in ("hebel", "spot"):
        eintraege = ergebnisse[label]
        gerettet = [e for e in eintraege if not e["waere_unter_neuer_regel_ueberholt"]]
        tp = [e for e in gerettet if e.get("simuliertes_ergebnis") == "take_profit_erreicht"]
        sl = [e for e in gerettet if e.get("simuliertes_ergebnis") == "stop_loss_erreicht"]
        nicht_pruefbar = [e for e in gerettet if e.get("simuliertes_ergebnis") == "nicht_pruefbar"]
        weiterhin_offen = len(gerettet) - len(tp) - len(sl) - len(nicht_pruefbar)

        print()
        print(f"=== {label.upper()} ===")
        print(f"Insgesamt ueberholte Signale im Export mit spaeterem realen Signal: {len(eintraege)}")
        print(f"Davon unter neuer Regel GERETTET (waeren weiter offen geblieben statt ueberholt): {len(gerettet)}")
        if gerettet:
            print(f"  davon Take-Profit erreicht: {len(tp)}")
            print(f"  davon Stop-Loss erreicht: {len(sl)}")
            print(f"  davon weiterhin offen bis zum ausloesenden Signal: {weiterhin_offen}")
            print(f"  davon nicht pruefbar (fehlende Zonen): {len(nicht_pruefbar)}")
        print(f"Neue Stichprobengroesse fuer historische Trefferquote (TP+SL): "
              f"{len(tp) + len(sl)} zusaetzlich zu den bisherigen echten Ergebnissen")
        print("Details:")
        for e in eintraege:
            print(" ", e)


if __name__ == "__main__":
    main()
