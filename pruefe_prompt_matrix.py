# -*- coding: utf-8 -*-
"""Steht jeder Parameter dort, wo die Matrix ihn hinschreibt? (17.08.2026)

DER ANLASS. Nutzervorgabe: *"die unterschiedlichen Zuordnungen der Parameter je
Asset und Handelsform bitte sauber zur Nachvollziehbarkeit dokumentieren -
sonst vermutet man Fehler, wo keine sind"*, und danach: *"mache fuer alle
zuletzt neu hinzugefuegten LLM-Parameter einen sauberen Ende-zu-Ende-Test und
eine detaillierte Fehler- und Promptanalyse."*

WAS DIESES WERKZEUG ANDERS MACHT ALS DIE BESTEHENDEN:

    pruefe_pakete.py           prueft EINZELTEILE - jede Funktion fuer sich
    simuliere_kette.py         prueft den DURCHLAUF - kommt eine Mail heraus
    pruefe_zahlen_in_prompts   prueft die FORM der Saetze - Zahlen, Etiketten
    diese Datei                prueft die ZUORDNUNG - steht der Parameter bei
                               der richtigen Rolle, Assetklasse UND Handelsform

DIE MATRIX WIRD AUSFUEHRBAR. Kapitel 66 des Umbauplans fuehrt sie als Tabelle;
hier steht dieselbe Tabelle als Code. Weicht der Betrieb ab, meldet dieses
Skript es - und man muss nicht raten, ob eine fehlende Zeile ein Fehler oder
eine begruendete Auslassung ist.

    Drei der letzten fuenf Funde waren keine Fehler, sondern Zuordnungen,
    deren Grund nirgends stand.

AUFRUF:
    python pruefe_prompt_matrix.py --db <NB-Backup>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- DIE MATRIX (Umbauplan Kapitel 66) -------------------------------------
#
# Je (Gruppe, Instrument): welche BLOECKE der Rolle BC MUESSEN Saetze tragen,
# und welche duerfen es NICHT. Was in keiner der beiden Mengen steht, ist
# datenabhaengig und wird nicht bewertet (z. B. `marken` - ohne genug
# Wendepunkte gibt es keine).
BC_MATRIX = {
    ("krypto", "spot"): {
        "muss": {"bestand", "verlauf", "umschlag"},
        "darf_nicht": {"hebelgeometrie", "finanzierung", "fundamental",
                       "referenz"},
    },
    ("krypto", "hebel"): {
        "muss": {"bestand", "verlauf", "hebelgeometrie", "umschlag"},
        "darf_nicht": {"fundamental", "referenz"},
    },
    ("aktien", "spot"): {
        "muss": {"bestand", "verlauf", "fundamental"},
        "darf_nicht": {"hebelgeometrie", "finanzierung", "umschlag"},
    },
    ("rohstoffe", "spot"): {
        "muss": {"bestand", "verlauf"},
        "darf_nicht": {"hebelgeometrie", "finanzierung", "fundamental",
                       "umschlag"},
    },
    ("themen_etf", "spot"): {
        "muss": {"bestand", "verlauf"},
        "darf_nicht": {"hebelgeometrie", "finanzierung", "fundamental",
                       "umschlag"},
    },
    ("hedge", "absicherung"): {
        "muss": {"bestand", "verlauf"},
        "darf_nicht": {"finanzierung", "fundamental", "umschlag"},
    },
}

# Rolle G, erkannt am WORTLAUT. Ein Feld daneben waere eine zweite Definition,
# die auseinanderlaufen kann - dieselbe Ueberlegung wie in `mindestkriterien`.
G_MERKMALE = {
    "terminmarkt": "offenen Kontrakte am Terminmarkt",
    "divergenz":   "Boersen entwickeln sich dabei",
    "funding":     "Die Finanzierungsrate steht",
    "long_anteil": "Anteil der Konten auf der Kaufseite",
    # ⚠️ ZWEI FORMEN, NICHT EINE. Der Satz lautet je nach Richtung
    # "flossen mehr Bitcoin AUF die Boersen" oder "VON den Boersen
    # herunter". Mein erstes Muster kannte nur die eine - und meldete an
    # einem Abflusstag eine Luecke, die keine war.
    "boersenfluss": "flossen mehr Bitcoin",
    "cot":         "US-Aufsicht meldet woechentlich",
    "short":       "Eindeckungsdauer",
    "insider":     "Insider meldeten",
}
G_MATRIX = {
    ("krypto", "spot"): {
        "muss": {"terminmarkt", "funding", "long_anteil", "boersenfluss"},
        "darf_nicht": {"cot", "short", "insider"},
    },
    # ⚠️ FUNDING FEHLT HIER ABSICHTLICH: beim Hebel steht es in Rolle BC
    # (R-R2 je Instrument, Kapitel 66.2). Das ist der Fall, den ohne diese
    # Datei jeder fuer einen Fehler halten wuerde.
    ("krypto", "hebel"): {
        "muss": {"terminmarkt", "long_anteil", "boersenfluss"},
        "darf_nicht": {"funding", "cot", "short", "insider"},
    },
    ("rohstoffe", "spot"): {
        "muss": {"cot"},
        "darf_nicht": {"terminmarkt", "funding", "boersenfluss", "short",
                       "insider"},
    },
    ("aktien", "spot"): {
        "muss": {"short"},          # Insider braucht den Job - nur "darf"
        "darf_nicht": {"terminmarkt", "funding", "boersenfluss", "cot"},
    },
    ("themen_etf", "spot"): {
        "muss": set(),
        "darf_nicht": set(G_MERKMALE),
    },
    ("hedge", "absicherung"): {
        "muss": set(),
        "darf_nicht": set(G_MERKMALE),
    },
}

# --- WAS EIN JOB LIEFERT, KANN IM TESTBESTAND FEHLEN -----------------
#
# Fundamentaldaten, Insider, Leerverkaeufer, COT und Boersenfluesse
# schreibt `externe_reihen_job`. Ein NB-Backup von vor dem Joblauf hat sie
# nicht - und dann fehlt der Satz VOELLIG ZU RECHT. Ohne diese
# Unterscheidung meldet die Matrix eine Luecke, wo nur die Testdatei aelter
# ist als die Verdrahtung: genau die Sorte Fehlalarm, gegen die sie
# gebaut wurde.
JOBABHAENGIG = {
    "fundamental":  ("yfinance", "_gewinnwachstum_pct"),
    "short":        ("finra", "_days_to_cover"),
    "insider":      ("sec_edgar", "_insider_verkaeufe"),
    "cot":          ("cftc_cot", ""),
    "boersenfluss": ("coinmetrics", ""),
}


def _quelle_vorhanden(conn, schluessel: str, symbol: str) -> bool:
    """Liegen die Rohdaten fuer diesen Parameter ueberhaupt vor?"""
    eintrag = JOBABHAENGIG.get(schluessel)
    if eintrag is None:
        return True                    # nicht jobabhaengig
    quelle, endung = eintrag
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM externe_reihe WHERE quelle = ? "
            "AND schluessel LIKE ?",
            (quelle, f"%{symbol}{endung}%" if endung else "%")).fetchone()[0]
    except sqlite3.Error:
        return False
    return n > 0


# Wie hoch der Anteil der Kerzenreihe in Rolle BC hoechstens sein DARF, bevor
# es gemeldet wird. Keine Regel, sondern ein Beobachtungswert: gemessen am
# 17.08. lag er bei Krypto Spot bei 90 % - und genau daran haengt der
# Grundbefund (nur das Momentum trennt Einstieg von Halten).
KERZENANTEIL_WARNUNG = 0.85
KERZENBLOECKE = ("verlauf", "marken", "hebelgeometrie", "volumen")


def _bc_bloecke(conn, db: str, symbol: str, gruppe: str, instrument: str):
    """Die Bloecke der Rolle BC fuer genau dieses Paar - wie im Betrieb."""
    import database.db as DB
    from agent import lagebeschreibung as LB
    from agent import rollen_eingabe as RE

    for waehrung in ("EUR", "USD"):
        reihe = DB.get_ohlc_history(conn, symbol, waehrung)
        if reihe and len(reihe) >= 120:
            break
    else:
        return None
    i = len(reihe) - 1
    h = [float(k.high) for k in reihe[-15:]]
    t = [float(k.low) for k in reihe[-15:]]
    atr = sum(a - b for a, b in zip(h, t)) / len(h)
    return LB.geteilt(
        symbol=symbol, reihe=reihe, index=i, kurs_eur=float(reihe[-1].close),
        atr=atr, instrument=instrument,
        fundamentaldaten=RE.fundamentaldaten(symbol, db, gruppe),
        umschlag=RE.umschlag(symbol, db, gruppe))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    a = p.parse_args()

    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    from agent import assetklassen as AK
    from agent import positionierung as PO
    import pruefe_zahlen_in_prompts as PZ

    gruppen = AK.gruppiere() or {}
    abweichungen: list[str] = []
    zahlenbefunde: list[tuple] = []

    print("=" * 78)
    print("ROLLE BC - welche Bloecke tragen Saetze?")
    print("=" * 78)
    print(f"{'Gruppe/Instrument':24}{'Symbol':9}{'Saetze':>7}{'Kerze':>7}  Bloecke")
    for (gruppe, instrument), regel in BC_MATRIX.items():
        symbole = [s for s in gruppen.get(gruppe, [])]
        gefunden = None
        for sym in symbole:
            bl = _bc_bloecke(conn, a.db, str(sym).upper(), gruppe, instrument)
            if bl and sum(len(v or []) for v in bl.values()) >= 3:
                gefunden = (str(sym).upper(), bl)
                break
        if not gefunden:
            abweichungen.append(f"{gruppe}/{instrument}: kein Symbol renderbar")
            print(f"{gruppe + '/' + instrument:24}{'-':9}{'-':>7}{'-':>7}  "
                  f"NICHT RENDERBAR")
            continue
        sym, bl = gefunden
        da = {b for b, v in bl.items() if v}
        n = sum(len(v or []) for v in bl.values())
        kerze = sum(len(bl.get(b) or []) for b in KERZENBLOECKE)
        anteil = kerze / n if n else 0.0
        print(f"{gruppe + '/' + instrument:24}{sym:9}{n:>7}{anteil:>6.0%}  "
              f"{', '.join(sorted(da))}")
        for b in regel["muss"] - da:
            if not _quelle_vorhanden(conn, b, sym):
                print(f"{'':24}{'':9}{'':>7}{'':>7}  (Block '{b}' ohne "
                      f"Rohdaten - Job lief gegen diese Datei nicht)")
                continue
            abweichungen.append(f"{gruppe}/{instrument} ({sym}): Block '{b}' "
                                f"FEHLT, die Matrix verlangt ihn")
        for b in regel["darf_nicht"] & da:
            abweichungen.append(f"{gruppe}/{instrument} ({sym}): Block '{b}' "
                                f"steht da, die Matrix verbietet ihn")
        if anteil > KERZENANTEIL_WARNUNG:
            abweichungen.append(
                f"{gruppe}/{instrument} ({sym}): {anteil:.0%} der Saetze aus "
                f"der Kerzenreihe - die entscheidende Rolle ist dort "
                f"unterernaehrt")
        for v in bl.values():
            for s in (v or []):
                f = PZ.pruefe_satz(s)
                if f:
                    zahlenbefunde.append((f"BC {gruppe}/{instrument}", s, f[0]))

    print()
    print("=" * 78)
    print("ROLLE G - welche Merkmale liegen vor?")
    print("=" * 78)
    print(f"{'Gruppe/Instrument':24}{'Symbol':9}{'Saetze':>7}  Merkmale")
    for (gruppe, instrument), regel in G_MATRIX.items():
        symbole = [s for s in gruppen.get(gruppe, [])]
        bestes = None
        for sym in symbole:
            lage = PO.lage(conn, str(sym).upper(), assetklasse=gruppe,
                           instrument=instrument)
            saetze = PO.saetze(lage)
            text = " ".join(saetze)
            da = {k for k, w in G_MERKMALE.items() if w in text}
            if bestes is None or len(da) > len(bestes[2]):
                bestes = (str(sym).upper(), saetze, da)
            if regel["muss"] <= da:
                break
        if not bestes:
            continue
        sym, saetze, da = bestes
        print(f"{gruppe + '/' + instrument:24}{sym:9}{len(saetze):>7}  "
              f"{', '.join(sorted(da)) or '-'}")
        for k in regel["muss"] - da:
            if not _quelle_vorhanden(conn, k, sym):
                print(f"{'':24}{'':9}{'':>7}  (Merkmal '{k}' ohne "
                      f"Rohdaten - Job lief gegen diese Datei nicht)")
                continue
            abweichungen.append(f"{gruppe}/{instrument} ({sym}): Merkmal "
                                f"'{k}' FEHLT, die Matrix verlangt es")
        for k in regel["darf_nicht"] & da:
            abweichungen.append(f"{gruppe}/{instrument} ({sym}): Merkmal "
                                f"'{k}' steht da, die Matrix verbietet es")
        for s in saetze:
            f = PZ.pruefe_satz(s)
            if f:
                zahlenbefunde.append((f"G {gruppe}/{instrument}", s, f[0]))

    print()
    print("=" * 78)
    if zahlenbefunde:
        print(f"FORMBEFUNDE ({len(zahlenbefunde)}):")
        for wo, s, f in zahlenbefunde[:10]:
            print(f"  [{wo}] {s[:76]}")
            print(f"        -> {f[:70]}")
    else:
        print("FORM: kein Satz rechnet dem Modell etwas vor.")
    print()
    if abweichungen:
        print(f"ABWEICHUNGEN VON DER MATRIX ({len(abweichungen)}):")
        for z in abweichungen:
            print(f"  ⚠️ {z}")
        return 1
    print("ZUORDNUNG: jeder Parameter steht dort, wo Kapitel 66 ihn hinschreibt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
