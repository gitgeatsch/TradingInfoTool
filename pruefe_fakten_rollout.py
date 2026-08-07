"""Findet Fakten und Mechanismen, die nur in einem Teil der Pipelines existieren.

ANLASS (07.08.2026). Nutzer-Einwand: *"bei den Multi- oder sonstigen Assets
genau achten, wo und wie diese umgesetzt wurden, u.U. haengen die noch Wochen
zurueck vom Code und Themenlage."* Nachgemessen: **von elf Fakten, die zwischen
dem 09.07. und dem 06.08. entstanden sind, wurde genau EINER auf alle fuenf
Spot-Klassen ausgerollt** (`crv_baender`, und der nur, weil er ausdruecklich so
gefordert war). Der Stand der Nicht-Krypto-Analysten entsprach im Kern dem
09.07.

DIE URSACHE war kein Versehen im Einzelfall, sondern ein Muster: jede
Erweiterung wurde dort gebaut, wo gerade gearbeitet wurde, und der Rollout auf
die uebrigen Klassen war nie Teil der Definition von "fertig".

WAS DIESES SKRIPT TUT. Es liest die `build_facts()`-Quelltexte aller sechs
Pipelines, sammelt die Faktenschluessel und meldet jeden, der in einer echten
TEILMENGE vorkommt. Dazu dieselbe Pruefung auf Pipeline-Ebene fuer eine Liste
bekannter Mechanismen.

WAS ES NICHT TUT, und das ist wichtig: es faellt **kein Urteil**. Viele
Unterschiede sind richtig - `btc_relativwert` gehoert nicht in die
Rohstoff-Pipeline, `hebel_kontext` nicht in Spot, und Hedge hat bewusst keine
technische Analyse. Das Skript stellt die FRAGE ("gilt das auch fuer die
anderen?"), die Antwort gehoert ins Entscheidungslog. Ein "gilt nur fuer
Krypto, weil X" ist ein gueltiges Ergebnis; ein stilles Auslassen nicht.

AUFRUF (keine DB noetig, reine Quelltextanalyse):
    python pruefe_fakten_rollout.py
    python pruefe_fakten_rollout.py --nur-neue   # nur Fakten seit einem Datum
"""
import importlib
import inspect
import re
import subprocess
import sys

# Pipeline -> (Analyst-Modul, build-Funktion, Analyst-Datei, Pipeline-Datei)
PIPELINES = {
    "krypto-spot": ("agent.krypto.analyst", "build_facts",
                    "agent/krypto/analyst.py", "agent/krypto/pipeline.py"),
    "hebel": ("agent.krypto.hebel_analyst", "build_hebel_facts",
              "agent/krypto/hebel_analyst.py", "agent/krypto/hebel_pipeline.py"),
    "aktien": ("agent.aktien.analyst", "build_facts",
               "agent/aktien/analyst.py", "agent/aktien/pipeline.py"),
    "themen_etf": ("agent.themen_etf.analyst", "build_facts",
                   "agent/themen_etf/analyst.py", "agent/themen_etf/pipeline.py"),
    "rohstoffe": ("agent.rohstoff.analyst", "build_facts",
                  "agent/rohstoff/analyst.py", "agent/rohstoff/pipeline.py"),
    "hedge": ("agent.hedge.analyst", "build_facts",
              "agent/hedge/analyst.py", "agent/hedge/pipeline.py"),
}

# Die fuenf Spot-Klassen - untereinander sollten sie am ehesten gleich sein.
# Hebel und Hedge haben eigene Logik, ihre Unterschiede sind haeufiger richtig.
SPOT_FAMILIE = ("krypto-spot", "aktien", "themen_etf", "rohstoffe")

# Mechanismen auf Pipeline-Ebene, erkannt am Vorkommen eines Bezeichners.
MECHANISMEN = {
    "Z.ai-Gegenpruefung": "fuehre_beide_calls_im_hintergrund",
    "Selbst-HALTEN-Tracking": "ist_reines_llm_halten",
    "original_action": "_original_action",
    "Risikofaktoren": "risikofaktoren",
    "Fazit-Konsistenz": "_fazit_konsistenz_hinweis",
    "Mindestziel": "mindestziel",
    "Ausstiegsregel": "ausstiegsregel",
    "Systemguete-Fakt": "fakt_systemguete",
    "CRV-Baender-Fakt": "fakt_crv_baender",
    "JIT-Historie": "jit_refresh_ohlc",
}

# Bewusste Ausnahmen: hier ist der Unterschied entschieden und dokumentiert.
# Ein Eintrag hier heisst NICHT "unwichtig", sondern "geprueft und begruendet".
BEGRUENDETE_UNTERSCHIEDE = {
    "btc_relativwert": "BTC-Bezug - fuer Aktien/Rohstoffe/ETF gegenstandslos",
    "hebel_kontext": "nur Hebel hat einen Hebelfaktor",
    "position_aktuell": "nur Hebel fuehrt offene Positionen",
    "trigger": "nur Hebel hat einen Screening-Trigger",
    "optionsmarkt": "Deribit deckt nur Krypto ab",
    "kosten": "Funding/Gebuehren fallen so nur bei Hebel an",
    "hedge_instrument": "nur Hedge",
    "portfolio_exposure": "nur Hedge - Positionsgroesse folgt dem Exposure",
    "technische_analyse": "fuer Hedge bewusst ausgeschlossen (siehe Modul-Docstring)",
    "asset": "Hedge nutzt hedge_instrument statt asset",
    "marktscan_reifegrad": "Marktscan gibt es nur fuer Krypto",
    "marktscan_mindestziel": "Marktscan gibt es nur fuer Krypto",
    "strategien_aktiv": "Strategie-Schalter gibt es nur fuer Krypto",
    "lagerbestaende": "nur Rohstoffe (EIA)",
    "makro_ueberlagerung": "nur Rohstoffe",
    "positionierung": "nur Rohstoffe (CFTC COT)",
    "sektor_rotation": "nur Themen-ETF",
    "fundamentaldaten": "nur Aktien",
    "insider_trading": "nur Aktien (SEC)",
    "short_interest_finra": "nur Aktien (FINRA)",
    "analysten_trend_finnhub": "nur Aktien (Finnhub)",
    "haltung": "Hebel fuehrt position_aktuell stattdessen",
    "regime_profil": "Profil-Schwellen gelten bisher nur fuer Krypto",
    "markt_kontext": "BTC-Dominanz/Fear-Greed - Krypto-spezifisch",
    "these_abgleich": "Kategorie-Thesen gibt es nur fuer die Multi-Asset-Klassen",
    "risiko_check": "Hebel/Hedge haben eigene Gate-Logik",
    "disclaimers": "in allen vorhanden",
}


def fakten_je_pipeline() -> dict[str, set[str]]:
    ergebnis = {}
    for name, (modul, fn, _, _) in PIPELINES.items():
        src = inspect.getsource(getattr(importlib.import_module(modul), fn))
        i = src.index("facts = {") if "facts = {" in src else src.index("return {")
        ergebnis[name] = set(re.findall(r'^\s{8}"(\w+)":', src[i:], re.M))
    return ergebnis


def erstes_datum(schluessel: str, datei: str) -> str | None:
    r = subprocess.run(
        ["git", "log", "--reverse", "--format=%ad", "--date=short", "-S",
         f'"{schluessel}":', "--", datei],
        capture_output=True, text=True).stdout.strip().splitlines()
    return r[0] if r else None


def main() -> int:
    fakten = fakten_je_pipeline()
    alle = sorted(set().union(*fakten.values()))
    namen = list(PIPELINES)

    print("=" * 78)
    print("FAKTEN-ROLLOUT ueber sechs Pipelines")
    print("=" * 78)
    print(f"\n{'Fakt':<30}" + "".join(f"{n[:9]:<11}" for n in namen))
    for f in alle:
        zeile = f"  {f:<28}"
        for n in namen:
            zeile += f"{('  X' if f in fakten[n] else '  -'):<11}"
        print(zeile)

    print("\n" + "-" * 78)
    print("ZU ENTSCHEIDEN - Fakt fehlt in einem Teil der SPOT-FAMILIE")
    print("-" * 78)
    offen = []
    for f in alle:
        hat = {n for n in SPOT_FAMILIE if f in fakten[n]}
        if not hat or len(hat) == len(SPOT_FAMILIE):
            continue
        if f in BEGRUENDETE_UNTERSCHIEDE:
            continue
        fehlt = [n for n in SPOT_FAMILIE if n not in hat]
        quelle = sorted(hat)[0]
        datum = erstes_datum(f, PIPELINES[quelle][2])
        offen.append((f, sorted(hat), fehlt, datum))

    if not offen:
        print("\n  Keine unbegruendeten Luecken in der Spot-Familie.")
    for f, hat, fehlt, datum in offen:
        print(f"\n  {f}")
        print(f"      vorhanden in : {', '.join(hat)}" + (f"   (seit {datum})" if datum else ""))
        print(f"      FEHLT in     : {', '.join(fehlt)}")
        print(f"      -> entscheiden und im Entscheidungslog festhalten: gilt das auch dort?")

    print("\n" + "-" * 78)
    print("MECHANISMEN auf Pipeline-Ebene")
    print("-" * 78)
    inhalt = {}
    for n, (_, _, _, pfad) in PIPELINES.items():
        with open(pfad, encoding="utf-8") as fh:
            inhalt[n] = fh.read()
    print(f"\n{'Mechanismus':<26}" + "".join(f"{n[:9]:<11}" for n in namen))
    luecken = 0
    for mname, muster in MECHANISMEN.items():
        vorhanden = {n for n in namen if muster in inhalt[n]}
        zeile = f"  {mname:<24}"
        for n in namen:
            zeile += f"{('  X' if n in vorhanden else '  -'):<11}"
        spot_fehlt = [n for n in SPOT_FAMILIE if n not in vorhanden]
        if vorhanden & set(SPOT_FAMILIE) and spot_fehlt:
            zeile += "  <== Luecke in der Spot-Familie"
            luecken += 1
        print(zeile)

    print("\n" + "=" * 78)
    print(f"{len(offen)} Fakten und {luecken} Mechanismen sind in der Spot-Familie ungleich verteilt.")
    print("Das ist KEIN Urteil - viele Unterschiede sind richtig. Es ist die Frage,")
    print("ob sie ENTSCHIEDEN wurden. Begruendete Faelle gehoeren in")
    print("BEGRUENDETE_UNTERSCHIEDE oben, damit sie hier nicht mehr auftauchen.")
    print("=" * 78)
    return 1 if (offen or luecken) else 0


if __name__ == "__main__":
    raise SystemExit(main())
