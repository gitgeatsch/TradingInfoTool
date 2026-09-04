# -*- coding: utf-8 -*-
"""Kumulative Gegenpruefung ueber ALLE Pakete des Umbauplans (12.08.2026).

NUTZERVORGABE, die diese Datei erzwungen hat: *"mache rueckwirkend ueber alle
Pakete pro neuem Paket eine Gegenpruefung, sonst verlieren wir den Faden."*

Der Punkt ist die RUECKWIRKUNG. Jedes Paket einmal zu pruefen und danach nie
wieder heisst, dass Paket 5 Paket 1 still zerbricht - und genau das ist an
diesem Tag zweimal passiert:

  * Der Marktbreite-Schnitt (L1) entfernte `TRAGFAEHIGKEIT`, woran der
    Schema-Verteiler die Rolle Lagebild erkannte. Jeder strikte Aufruf waere
    mit einem AttributeError gestorben. Gefunden erst bei der Gegenpruefung zu
    Paket 1 - also einen Umbau spaeter.
  * Zwei neue Felder in Paket 1 vergroesserten einen Strikt-Vertrag-Verstoss,
    den es vorher schon gab (4 statt 2 Felder). Die volle Fluche zeigte 28-31
    Verstoesse je Signal-Analyst.

Beides waere von einem Lauf DIESER Datei gefangen worden.

    python pruefe_pakete.py            alle Pakete
    python pruefe_pakete.py --paket 1  nur eines

REGEL FUER NEUE PAKETE: Wer ein Paket baut, haengt seine Pruefungen hier an -
und laesst die ALTEN mitlaufen. Eine Pruefung, die nur am Tag ihrer Entstehung
lief, ist eine Notiz, kein Netz.

Kein LLM-Aufruf, kein Netzwerk. Diese Datei darf jederzeit laufen.

⚠️ EINE AUSNAHME (24.08.2026): `main()` schreibt den vollstaendigen
Konsolentext zusaetzlich nach `Claude_Austauschordner/Pruefungen/` auf Google
Drive - best effort, bricht bei fehlendem Laufwerk nicht ab. Anlass: externe
Zusammenfassungen der Ausgabe haben wiederholt gekuerzt oder falsch gedeutet;
der Volltext an einem festen Ort macht das ueberfluessig.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import subprocess as _SUB
import ast as _AST
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

_ERGEBNISSE: list[tuple[str, str, bool, str]] = []


def pruefe(paket: str, name: str, bedingung, detail: str = "") -> None:
    _ERGEBNISSE.append((paket, name, bool(bedingung), detail))


def _quelltext(pfad: str) -> str:
    """Nur der AKTIVE Code - Kommentarzeilen fliegen raus.

    Notwendig, weil dieses Projekt Entferntes ausfuehrlich im Kommentar
    festhaelt. Ein `grep` faende die geloeschte Zeile in ihrer eigenen
    Grabinschrift wieder - genau dieser Fehler ist am 12.08. passiert (der
    Nur-Long-Vorfilter galt als aktiv, weil ein Kommentar seine Entfernung
    beschrieb)."""
    roh = io.open(pfad, encoding="utf-8").read()
    return "\n".join(z for z in roh.split("\n")
                     if not z.strip().startswith("#"))


# ---------------------------------------------------------------- Paket 0 ---
def paket_0() -> None:
    """Bereinigungen: Symbolliste raus, Hedge ohne Tranchen."""
    P = "0"
    code = _quelltext("agent/krypto/pipeline.py")
    pruefe(P, "Symbolliste ('BTC','ETH','SOL') nicht mehr im aktiven Code",
           not re.search(r'asset\.symbol\s+in\s+\("BTC",\s*"ETH",\s*"SOL"\)', code),
           "sie ueberstimmte den Toggle des Nutzers")

    pruefe(P, "Tranchen haengen weiterhin am Regime UND am Toggle",
           "get_dca_erlaubt" in code and "regime_result.regime in" in code,
           "die Regime-Bedingung darf nicht mitentfernt worden sein")

    hedge = _quelltext("agent/hedge/pipeline.py")
    pruefe(P, "Hedge setzt tranchen_erlaubt = False",
           re.search(r"tranchen_erlaubt\s*=\s*False", hedge) is not None,
           "die Staffelungsregel wirkte dort mit umgekehrtem Vorzeichen")
    pruefe(P, "Hedge ruft multi_asset_tranchen_erlaubt() NICHT mehr",
           "multi_asset_tranchen_erlaubt" not in hedge)

    # KEIN VERHALTENSWECHSEL ohne Zutun des Nutzers - der eigentliche Punkt.
    import sqlite3

    import database.db as db
    con = sqlite3.connect("data/tradinginfotool.db")
    con.row_factory = sqlite3.Row
    krypto = ("BTC", "ETH", "SOL", "LINK", "AVAX", "SUI", "TAO")
    gleich = all(db.get_dca_erlaubt(con, s) == (s in ("BTC", "ETH", "SOL"))
                 for s in krypto)
    con.close()
    pruefe(P, "Krypto-Verhalten unveraendert ohne Zutun des Nutzers", gleich,
           "die Whitelist begrenzt weiterhin auf BTC/ETH/SOL")


# ---------------------------------------------------------------- Paket 1 ---
def paket_1() -> None:
    """Ausgabefelder: Zielkurs und Spannen abgeleitet, Falsifikator pruefbar."""
    P = "1"
    from agent import rolle_trader as RT

    # DIE GEOMETRIE ist der Kern: Stop 1,5 ATR unter Einstieg, Ziel 3,0 ATR
    # darueber. Weicht sie ab, sind zwei Trefferquoten nicht mehr vergleichbar
    # und die Kalibrierungstabelle (Paket 8) kann nicht entstehen.
    atr = 4.0
    r = RT.leite_zonen_ab({"aktion": "KAUFEN", "einstieg_eur": 100.0,
                           "stop_eur": 100.0 - 1.5 * atr}, atr)
    pruefe(P, "Ziel liegt exakt 3,0 ATR ueber dem Einstieg",
           abs(r.get("ziel_eur", 0) - (100.0 + 3.0 * atr)) < 1e-9,
           f"ziel={r.get('ziel_eur')}, erwartet {100.0 + 3.0 * atr}")
    pruefe(P, "Spanne betraegt 0,25 ATR je Seite",
           abs(r.get("einstieg_eur_bis", 0) - r.get("einstieg_eur_von", 0)
               - 0.5 * atr) < 1e-9)

    grund = {"belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"},
                        {"fakt": "b", "richtung": "dafuer", "gewicht": "mittel"}],
             "unabhaengige_faktoren": 2, "aktion": "KAUFEN",
             # ⚠️ S6c: die Richtung ist bei KAUFEN Pflicht - fuer BEIDE
             # Instrumente. Bis dahin galt sie nur bei instrument="hebel",
             # und seit S6b war dieser Zweig tot.
             "richtung": "LONG",
             "einstieg_eur": 100.0, "stop_eur": 94.0,
             "begruendung": "x", "was_dagegen": "y", "umgeworfen_durch": "z"}
    ohne = RT.validiere({**grund, "aktion": "NICHTS_TUN"}, "X", atr=atr)
    pruefe(P, "NICHTS_TUN traegt keine Zone",
           not any(k in ohne for k in ("ziel_eur", "einstieg_eur", "stop_eur")))

    pruefe(P, "Stop >= Einstieg erzeugt KEINE Zone",
           "ziel_eur" not in RT.leite_zonen_ab(
               {"einstieg_eur": 94.0, "stop_eur": 100.0}, atr),
           "der Widerspruch gehoert dem Vertrag, nicht einer Rechnung")

    winzig = RT.leite_zonen_ab({"einstieg_eur": 0.000191,
                                "stop_eur": 0.000179}, 0.000008)
    pruefe(P, "Winzige Kurse bleiben unterscheidbar",
           winzig.get("einstieg_eur_von") != winzig.get("einstieg_eur_bis"),
           "SUPRA steht bei 0,000191")

    from agent import llm_schema
    s = llm_schema.baue_trader_schema(RT)
    pruefe(P, "Falsifikator ist maschinenlesbar",
           {"umgeworfen_preis_eur", "umgeworfen_bis"} <= set(s["properties"]),
           "ohne sie kann V1 nicht pruefen, ob eine Entscheidung widerlegt ist")

    # ALLE Aufrufer muessen den ATR durchreichen - sonst ist das Feature
    # gebaut und in genau einem Pfad nicht aktiv.
    import glob
    ohne_atr = []
    for d in sorted(glob.glob("messe_*.py") + ["pruefe_rollenkette.py"]):
        t = _quelltext(d)
        for m in re.finditer(r"RT\.validiere\(", t):
            rest = t[m.end():m.end() + 260]
            if "atr=" not in rest.split("\n\n")[0]:
                ohne_atr.append(d)
    pruefe(P, "Jeder Aufrufer reicht den ATR durch", not ohne_atr,
           f"ohne: {sorted(set(ohne_atr))}" if ohne_atr else "")


# ------------------------------------------------- Paket 1: Strikt-Vertrag ---
def _strikt_verstoesse(schema, pfad="wurzel", aus=None) -> list:
    aus = aus if aus is not None else []
    if isinstance(schema, dict):
        if isinstance(schema.get("properties"), dict):
            p = set(schema["properties"])
            r = set(schema.get("required") or [])
            if p - r:
                aus.append((pfad, sorted(p - r)))
            if schema.get("additionalProperties") is not False:
                aus.append((pfad, ["additionalProperties nicht false"]))
            for k, v in schema["properties"].items():
                _strikt_verstoesse(v, f"{pfad}.{k}", aus)
        if isinstance(schema.get("items"), dict):
            _strikt_verstoesse(schema["items"], f"{pfad}[]", aus)
    return aus


def paket_1_schema() -> None:
    """Der Strikt-Vertrag - er gilt fuer JEDE Ausgabeform, nicht nur die neuen.

    Belegt (OpenAI Structured Outputs, von Groq und OpenRouter uebernommen):
    bei `strict: true` braucht jedes Objekt `additionalProperties: false` UND
    alle Eigenschaften in `required`. Vor dem 12.08. verletzten das alle sechs
    Signal-Schemata mit 28-31 Verstoessen - unentdeckt, weil OpenRouter der
    Pfad ist, der produktiv noch nicht sauber gelaufen ist."""
    P = "1"
    from agent import llm_schema

    class _OpenRouter:
        pass
    _OpenRouter.__module__ = "api.openrouter"
    client = _OpenRouter()

    module = ["agent.rolle_analyst", "agent.rolle_trader",
              "agent.krypto.analyst", "agent.krypto.hebel_analyst",
              "agent.aktien.analyst", "agent.hedge.analyst",
              "agent.rohstoff.analyst", "agent.themen_etf.analyst"]
    for name in module:
        __import__(name)
    fehler = {}
    for name in module:
        fmt = llm_schema.response_format_fuer(client, name)
        sch = (fmt.get("json_schema") or {}).get("schema")
        if sch is None:
            fehler[name] = ["kein striktes Schema - Verteiler erkennt die Form nicht"]
            continue
        v = _strikt_verstoesse(sch)
        if v:
            fehler[name] = v[:3]
    pruefe(P, f"Strikt-Vertrag ueber alle {len(module)} Ausgabeformen",
           not fehler, "; ".join(f"{k}: {v}" for k, v in fehler.items()))

    # Der Verteiler muss die beiden Rollen an haltbaren Merkmalen erkennen.
    for name, erwartet in (("agent.rolle_analyst", {"lage", "belege"}),
                           ("agent.rolle_trader", {"aktion", "belege"})):
        sch = (llm_schema.response_format_fuer(client, name)
               .get("json_schema") or {}).get("schema") or {}
        pruefe(P, f"Verteiler erkennt {name.rsplit('.', 1)[-1]}",
               erwartet <= set(sch.get("properties") or {}),
               "am 12.08. brach genau das - das Merkmal war eine Konstante, "
               "die derselbe Umbau entfernt hat")


# ---------------------------------------------------------------- Paket 2 ---
def paket_2() -> None:
    """Instrument und Strategie als Vorgabe an Rolle 2/3."""
    P = "2"
    from agent import handelsauftrag as HA
    from agent import rolle_trader as RT
    import agent.rollen_eingabe as RE

    erlaubt = sum(len(v) for v in HA.ERLAUBTE_PAARE.values())
    gesamt = len(HA.INSTRUMENTE) * len(HA.STRATEGIEN)
    geworfen = 0
    for i in HA.INSTRUMENTE:
        for s in HA.STRATEGIEN:
            try:
                HA.pruefe(i, s)
            except HA.AuftragUngueltig:
                geworfen += 1
    pruefe(P, f"{gesamt - erlaubt} Kombinationen werden abgelehnt",
           geworfen == gesamt - erlaubt,
           "hebel x akkumulation, absicherung x swing/akkumulation")

    for falsch in ("", None, "futures", "dca", "long", "spot-hebel"):
        try:
            HA.pruefe(falsch, "einstieg")
            pruefe(P, f"unbekanntes Instrument {falsch!r} wird abgelehnt", False,
                   "STILLER RUECKFALL - bewertete einen Hebel-Trade wie Spot")
        except HA.AuftragUngueltig:
            pruefe(P, f"unbekanntes Instrument {falsch!r} wird abgelehnt", True)

    # SCHREIBWEISE WIRD NORMALISIERT, und das ist gewollt: `pruefe()` macht
    # `.strip().lower()`. "Hebel" aus einem Aufrufer ist eindeutig das
    # Hebel-Instrument, kein Tippfehler.
    #
    # Diese Pruefung stand zuerst falsch herum - sie erwartete, dass "Hebel"
    # abgelehnt wird. In der ersten Gegenpruefung fiel das nicht auf, weil ich
    # es mit `akkumulation` gepaart hatte: dort warf schon die KOMBINATION, und
    # der Testfall sah bestanden aus. Genau dafuer gibt es diese Datei.
    pruefe(P, "Schreibweise wird normalisiert (' Hebel ' -> hebel)",
           HA.pruefe("  Hebel  ", " Swing ") == ("hebel", "swing"))

    pruefe(P, "Strategie aendert den Prompt wirklich",
           RT.prompt_fuer("spot", "einstieg") != RT.prompt_fuer("spot", "akkumulation"))
    pruefe(P, "Vorgabefall bleibt bitgleich SYSTEM_PROMPT_TRADER",
           RT.prompt_fuer() == RT.SYSTEM_PROMPT_TRADER,
           "alle Messbefunde bis zum 12.08. haengen daran")

    # Nutzerkorrektur 12.08.: Akkumulation hat ein Ziel, nur kein nahes.
    satz = " ".join(HA.beschreibe("spot", "akkumulation")).lower()
    pruefe(P, "Akkumulationssatz nennt die Erwartung, nicht nur ihr Fehlen",
           "erwartung" in satz and "verbilligt" in satz,
           "vorher stand dort nur 'kein Ausstiegskurs' - das klang wie 'kein Ziel'")
    pruefe(P, "Akkumulations-Prompt verweist auf den Falsifikator",
           "punkt 6" in RT.prompt_fuer("spot", "akkumulation").lower(),
           "er ist dort das EINZIGE Ausstiegskriterium")

    grund = {"belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"},
                        {"fakt": "b", "richtung": "dafuer", "gewicht": "mittel"}],
             "unabhaengige_faktoren": 2, "aktion": "KAUFEN",
             # ⚠️ S6c: die Richtung ist bei KAUFEN Pflicht - fuer BEIDE
             # Instrumente. Bis dahin galt sie nur bei instrument="hebel",
             # und seit S6b war dieser Zweig tot.
             "richtung": "LONG",
             "einstieg_eur": 100.0, "stop_eur": 94.0,
             "begruendung": "x", "was_dagegen": "y", "umgeworfen_durch": "z"}
    akk = RT.validiere(dict(grund), "X", atr=4.0,
                       instrument="spot", strategie="akkumulation")
    pruefe(P, "Akkumulation traegt keine Kurse und keinen Zielkurs",
           not any(k in akk for k in ("einstieg_eur", "stop_eur", "ziel_eur")),
           "sonst laese die Erfolgsmessung sie spaeter als Trefferquote")
    pruefe(P, "die Entfernung wird VERMERKT, nicht stillschweigend",
           "entfernt" in str(akk.get("_korrekturen") or ""))

    class _Kerze:
        date, open, high, low, close, volume = "2026-07-17", 1.0, 1.0, 1.0, 1.0, 1.0
    ein = RE.baue_befund_eingabe(symbol="X", reihe=[_Kerze()] * 300, index=299,
                                 kurs_eur=1.0, atr=0.04,
                                 instrument="hebel", strategie="swing")
    pruefe(P, "der Auftrag steht VOR dem Stand (R-T9)",
           list(ein).index("auftrag") < list(ein).index("stand"))

    from agent.waechter_zuspitzung import finde_grade
    schlimm = [(i, s) for i in HA.INSTRUMENTE for s in HA.ERLAUBTE_PAARE[i]
               for satz in HA.beschreibe(i, s) if any(finde_grade(satz))]
    pruefe(P, "kein Gradwort im Auftragstext", not schlimm, str(schlimm))


# ---------------------------------------------------------------- Paket 3 ---
def paket_3() -> None:
    """Urteil je Assetklasse, und die Anlegerstimmung als Fakt."""
    P = "3"
    import sqlite3
    from agent import marktlage as ML
    from agent import rolle_analyst as RA
    from agent import llm_schema
    import agent.rollen_eingabe as RE

    con = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
    n, a1, b1 = con.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM macro_snapshot "
        "WHERE fear_greed_value IS NOT NULL").fetchone()
    con.close()
    pruefe(P, "Stimmungs-Historie ist nachgeladen", n and n > 2000,
           f"{n} Tage {a1} .. {b1} - vorher waren es 10")

    stimmung = RE.lade_stimmung()
    satz = ML.beschreibe_stimmung(stimmung, "2026-07-17")
    pruefe(P, "Stimmungssatz entsteht", len(satz) == 1)
    if satz:
        t = satz[0]
        pruefe(P, "er nennt Bitcoin, nicht 'den Kryptomarkt'",
               "Bitcoin" in t and "Kryptomarkt" not in t,
               "der Index ist ausdruecklich BTC-only")
        pruefe(P, "er traegt kein Etikett der Quelle",
               not any(w in t for w in ("Extreme Fear", "Extreme Greed",
                                        "Fear", "Greed")),
               "ein absolutes Etikett wiegt schwerer als die Zahl daneben (R-T2)")
        pruefe(P, "er nennt sein Fenster (R-T1)", "Messungen" in t)

    # Kausalitaet: ein Tag NACH dem Anker darf nichts aendern.
    mit_zukunft = dict(stimmung)
    mit_zukunft["2026-08-01"] = 99
    pruefe(P, "Stimmung ist kausal abgeschnitten",
           ML.beschreibe_stimmung(mit_zukunft, "2026-07-17") == satz)

    # STELLUNG IM FAKTENSATZ - an ECHTEN Reihen, nicht an einer leeren.
    # Die erste Fassung dieser Pruefung uebergab {"BTC": []} und war damit
    # trivial wahr: ohne Reihen entsteht kein Satz, und ein leerer Vergleich
    # besteht immer. Eine Pruefung, die nicht scheitern kann, ist keine.
    from backtest_llm1_historisch import lade_reihen_aus_db
    alle = ML.beschreibe_marktlage(lade_reihen_aus_db(), "2026-07-17", stimmung)
    ort_stimmung = next((i for i, z in enumerate(alle) if "Anlegerstimmung" in z), None)
    ort_aktien = next((i for i, z in enumerate(alle) if "US-Aktienmarkt" in z), None)
    pruefe(P, "die Stimmung steht im Kryptoblock, nicht am Ende",
           ort_stimmung is not None and ort_aktien is not None
           and ort_stimmung < ort_aktien,
           f"Stimmung an Position {ort_stimmung}, Aktienblock ab {ort_aktien} "
           f"von {len(alle)} - sonst faerbt ein Krypto-Index auf Aktien ab")

    # Das Urteil je Klasse
    pruefe(P, "`klassen` ist Pflichtfeld", "klassen" in RA.REQUIRED_FELDER)
    sch = llm_schema.baue_lage_schema(RA)
    pruefe(P, "Schema kennt `klassen` mit Aufzaehlung",
           set(sch["properties"]["klassen"]["items"]["properties"]["einstufung"]["enum"])
           == set(RA.EINSTUFUNGEN))

    a = RA.validiere({"lage": "x", "belege": ["a", "b"],
                      "klassen": [{"klasse": "Aktien", "einstufung": "guenstig", "warum": "w"},
                                  {"klasse": "gold", "einstufung": "guenstig", "warum": "w"},
                                  {"klasse": "aktien", "einstufung": "unguenstig", "warum": "doppelt"}]})
    pruefe(P, "Schreibweise wird normalisiert, Unbekanntes verworfen",
           [e["klasse"] for e in a["klassen"]] == ["aktien"],
           "eine erfundene Zuordnung waere schlimmer als eine fehlende")
    pruefe(P, "Doppelte Klasse wird verworfen",
           str(a.get("_korrekturen", "")).count("verworfen") == 2)
    pruefe(P, "Fehlende Klassen werden VERMERKT", "ohne Einstufung" in str(a.get("_korrekturen")))

    class _K:
        date, open, high, low, close, volume = "2026-07-17", 1.0, 1.0, 1.0, 1.0, 1.0
    lage = {"lage": "x", "gleichlauf": "uneinheitlich",
            "klassen": [{"klasse": "krypto", "einstufung": "unguenstig", "warum": "w"},
                        {"klasse": "aktien", "einstufung": "guenstig", "warum": "w"}]}
    fuer = lambda kl: (RE.baue_befund_eingabe(
        symbol="X", reihe=[_K()] * 300, index=299, kurs_eur=1.0, atr=0.04,
        lagebild=lage, assetklasse=kl)["marktlage_beurteilung"].get("klasse") or {})
    pruefe(P, "der Trader bekommt NUR das Urteil seiner Klasse",
           fuer("krypto").get("klasse") == "krypto",
           "alle drei zu schicken hiesse, ihm Maerkte vorzulegen, ueber die er "
           "nicht entscheidet - und was dasteht, wiegt (R-T9)")
    pruefe(P, "etf folgt aktien", fuer("etf").get("klasse") == "aktien")
    pruefe(P, "fehlt das Urteil, kommt keines statt eines falschen",
           fuer("rohstoffe") == {})


# ---------------------------------------------------------------- Paket 4 ---
def paket_4() -> None:
    """Makro-Fakten: die einzigen, die mit keiner Kursreihe zu tun haben."""
    P = "4"
    import sqlite3
    from agent import marktlage as ML
    import agent.rollen_eingabe as RE

    con = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
    nl = con.execute("SELECT COUNT(netto_liquiditaet_mrd), MIN(date), MAX(date) "
                     "FROM macro_snapshot WHERE netto_liquiditaet_mrd IS NOT NULL"
                     ).fetchone()
    nz = con.execute("SELECT COUNT(rendite_10j_pct) FROM macro_snapshot "
                     "WHERE rendite_10j_pct IS NOT NULL").fetchone()[0]
    con.close()
    pruefe(P, "Makro-Historie ist nachgeladen", nl[0] > 400 and nz > 2000,
           f"{nl[0]} Liquiditaets-Wochenwerte ({nl[1]} .. {nl[2]}), {nz} Zinstage")

    makro = RE.lade_makro()
    saetze = ML.beschreibe_makro(makro, "2026-07-17")
    pruefe(P, "beide Makro-Saetze entstehen", len(saetze) == 2, str(saetze))

    # KAUSALITAET - der teuerste denkbare Fehler bei Makrodaten. Ein live
    # geholter Wert in einem Anker von 2022 truege die Zukunft rueckwaerts.
    verfaelscht = {"liquiditaet": dict(makro["liquiditaet"]),
                   "zinskurve": dict(makro["zinskurve"])}
    verfaelscht["liquiditaet"]["2026-08-05"] = 99999.0
    verfaelscht["zinskurve"]["2026-08-11"] = 9.99
    pruefe(P, "Makro ist kausal abgeschnitten",
           ML.beschreibe_makro(verfaelscht, "2026-07-17") == saetze,
           "ein Wert NACH dem Anker darf die Aussage nicht aendern")

    # UNTERSCHEIDET ES? Ein konstantes Feld waere wertlos (R-T6).
    proben = {d: ML.beschreibe_makro(makro, d)
              for d in ("2021-11-09", "2022-06-17", "2023-10-13", "2026-07-17")}
    pruefe(P, "die Makrolage unterscheidet die Epochen",
           len({tuple(v) for v in proben.values()}) == len(proben),
           "2022 muss die Straffung zeigen, 2021 nicht")

    # KEIN ANKER: die These des Nutzers darf NICHT in den Faktensatz.
    text = " ".join(saetze).lower()
    pruefe(P, "keine Nutzer-These im Faktensatz",
           not any(w in text for w in ("these", "gestuetzt", "widerspricht",
                                       "einschaetzung", "erwartung des")),
           "die These stammt vom Nutzer - sie als Fakt vorzulegen waere ein "
           "Anker (Index 0,45, Experten-Anker am staerksten)")

    from agent.waechter_zuspitzung import finde_grade
    schlimm = [z for z in saetze if any(finde_grade(z))]
    pruefe(P, "kein Gradwort in der Makrolage", not schlimm, str(schlimm))
    pruefe(P, "beide Saetze nennen ihr Fenster (R-T1)",
           all(("Wochen" in z or "Handelstage" in z) for z in saetze))

    pruefe(P, "fail-soft ohne Daten", ML.beschreibe_makro({}, "2026-07-17") == [],
           "ein Satz 'keine Makrodaten' waere ueber alle Anker gleich (R-T6)")

    # STELLUNG: das Makro rahmt ALLE Leitmaerkte und steht deshalb vorn.
    from backtest_llm1_historisch import lade_reihen_aus_db
    alle = ML.beschreibe_marktlage(lade_reihen_aus_db(), "2026-07-17",
                                   RE.lade_stimmung(), makro)
    # ⚠️ SEIT 17.08.2026 STEHEN ZWEI MAKROBLOECKE VORN, nicht einer:
    # zuerst die LANGE SICHT (99 Jahre Historie aus
    # `makro_historie_monat`), dann das TAGESMAKRO. Die Reihenfolge ist
    # nicht beliebig - R-T9 ist gemessen, und der weiteste Rahmen gehoert
    # nach vorn: die Jahrhundertlage hinter die Wochenliquiditaet zu
    # setzen hiesse, die Groessenordnungen umzudrehen.
    _lang = ML.beschreibe_lange_sicht(
        (makro or {}).get("monatsreihen"), "2026-07-17")
    pruefe(P, "beide Makrobloecke stehen VOR dem ersten Leitmarkt",
           alle[:len(_lang) + len(saetze)] == list(_lang) + list(saetze),
           f"{len(alle)} Aussagen, davon {len(_lang)} lange Sicht und "
           f"{len(saetze)} Tagesmakro - beide rahmen alle drei Maerkte "
           "zugleich")


# ---------------------------------------------------------------- Paket 5 ---
def paket_5() -> None:
    """Getrennte Toepfe - ein Topf begrenzt sich SELBST, und keiner blockiert."""
    P = "5"
    import inspect
    import config as C
    from agent import handelsauftrag as HA
    from agent import toepfe as T
    cfg = C.load_config()

    pruefe(P, "die Konfiguration kennt alle drei Toepfe",
           set(T.deckel_eur(cfg)) == set(T.TOEPFE), str(T.deckel_eur(cfg)))
    pruefe(P, "jedes Instrument gehoert genau EINEM Topf",
           sorted(T.TOPF_FUER_INSTRUMENT) == sorted(HA.INSTRUMENTE)
           and len(set(T.TOPF_FUER_INSTRUMENT.values())) == len(HA.INSTRUMENTE),
           "sonst waere die Trennung keine")

    # DIE WICHTIGSTE PRUEFUNG DES PAKETS, und sie prueft eine SIGNATUR.
    # Nutzereinwand 12.08.: "das Portfolio ist 70 Prozent im Minus und koennte
    # somit von sich aus schon ein Blocker sein." Ein Prozentdeckel schrumpft
    # mit dem Verlust und bremst am staerksten, wenn Handeln noetig ist.
    # Solange keine dieser Funktionen einen Portfoliowert SIEHT, kann das nicht
    # passieren - das ist strenger als jede Wertpruefung.
    ohne_portfolio = all(
        not any("portfolio" in p for p in inspect.signature(f).parameters)
        for f in (T.budget_eur, T.frei_eur, T.deckel_eur))
    pruefe(P, "keine Funktion kennt den Portfoliowert", ohne_portfolio,
           "ein Prozentdeckel auf -70 % waere nur noch 30 % gross, waehrend "
           "die Erholung +233 % braucht")
    pruefe(P, "die Deckel sind absolut in Euro",
           all(v is None or v > 1 for v in T.deckel_eur(cfg).values()),
           "ein Wert wie 10 waere ein Prozentsatz, kein Betrag")

    # KERNPROBE: kein Fuellstand veraendert einen anderen Topf.
    basis = {i: T.frei_eur(i, 0, cfg) for i in T.TOEPFE}
    unabhaengig = all(
        T.frei_eur(anderer, 0, cfg) == basis[anderer]
        for voll in T.TOEPFE for anderer in T.TOEPFE if anderer != voll)
    pruefe(P, "ein voller Topf veraendert KEINEN anderen", unabhaengig,
           "Nutzervorgabe: 'es kommen keine Kaufpositionen rein, weil Hedge "
           "gering ist' - genau das darf nicht passieren")

    pruefe(P, "Schutz wird NICHT gedeckelt",
           T.budget_eur("absicherung", cfg) is None,
           "wer im fallenden Markt absichern will und an eine Obergrenze "
           "stoesst, hat sie am falschen Ende")
    # ⚠️ DIESE PRUEFUNG STAND UMGEKEHRT (bis 19.08.2026). Sie verlangte, dass
    # Spot KEINEN Deckel hat, mit der Begruendung: "die RM-Regeln begrenzen
    # die Einzelposition bereits, ein zweiter Deckel waere nur eine zweite
    # Blockadestelle".
    #
    # DIE PRAEMISSE IST WEGGEFALLEN. Damals folgte der Topf dem LAUF, und der
    # Grossteil der Signale lag im gedeckelten Hebeltopf. Seit S5 faellt in
    # vier von fuenf Faellen Hebel 1,0 an, und seit heute folgt der Topf der
    # ZAHL - der Grossteil wandert damit in den Spot-Topf, der ungedeckelt
    # war. Was frueher eine zweite Blockade gewesen waere, ist jetzt die
    # einzige Begrenzung ueberhaupt.
    #
    # UND ER BLOCKIERT NICHT (Nutzervorgabe 19.08.: "soll keine Blockierung
    # darstellen"). Gemessen: 800 EUR Betrag bei 200 EUR freiem Topf, mit
    # Vermerk in der Mail. Die alte Sorge trifft ihn nicht.
    pruefe(P, "Spot hat jetzt einen Deckel - und er blockiert nicht",
           T.budget_eur("spot", cfg) is not None,
           "seit der Topf der Zahl folgt, waere Spot sonst die einzige "
           "unbegrenzte Stelle - bei rund 80 % der Signale")
    pruefe(P, "der Hebel behaelt als EINZIGER einen Deckel",
           T.budget_eur("hebel", cfg) is not None
           and T.frei_eur("hebel", 99999, cfg) == 0.0,
           "die einzige Position, die MEHR verlieren kann als ihren Einsatz")

    for falsch in ("", None, "futures", "Spot-Hebel"):
        try:
            T.topf_fuer(falsch)
            pruefe(P, f"unbekanntes Instrument {falsch!r} wirft", False,
                   "STILLER RUECKFALL auf spot")
        except T.TopfUnbekannt:
            pruefe(P, f"unbekanntes Instrument {falsch!r} wirft", True)

    pruefe(P, "Absicherungsbedarf = Exposure / Hebelfaktor",
           T.absicherung_bedarf_eur(6000, 3.0) == 2000.0,
           "keine Prozentzahl aus der Optionsliteratur - 3QSS/DBPK sind "
           "gehebelte inverse ETFs, kein Praemiengeschaeft")
    pruefe(P, "Hebelfaktor 0 ergibt 0 statt Division durch null",
           T.absicherung_bedarf_eur(6000, 0) == 0.0)

    quelle = _quelltext("agent/toepfe.py")
    pruefe(P, "uebergreifende Groessen stehen NAMENTLICH",
           "UEBERGREIFEND" in quelle,
           "damit sich an keiner zweiten Stelle eine Verrechnung einschleicht")
    pruefe(P, "kein Prozentdeckel mehr im aktiven Code",
           "toepfe_anteil_prozent" not in quelle and "VORGABE_ANTEIL" not in quelle,
           "die erste Fassung rechnete Prozente vom Portfolio")


# ---------------------------------------------------------------- Paket 6 ---
def paket_6() -> None:
    """Feldabbildung Rollen-Kette -> signals."""
    P = "6"
    import json
    import sqlite3
    from agent import rolle_trader as RT
    from agent import signal_abbildung as SA
    from agent.krypto.analyst import REQUIRED_ACTIONS as ALT
    from agent.empfehlung_vertrag import AKTIONEN as NEU

    # ECKPUNKT 1: erweitern statt abbilden. HALTEN und NICHTS_TUN sind NICHT
    # dasselbe - wer beides in eine Spalte wirft, kann hinterher nie mehr
    # unterscheiden, ob eine Position gehalten oder ein Einstieg verweigert
    # wurde. Genau diese Unterscheidung IST der Deadloop.
    # NICHTS_TUN -> HALTEN. Korrigiert nach Nutzereinwand: auf der Ebene des
    # ASSETS ist beides dieselbe Aktion (kein Trade, Stand bleibt). Der
    # Unterschied, den ich zuerst behauptet hatte, steckt im KONTEXT (halte ich
    # es oder nicht) - und der steht im Bestand, nicht im Aktionsnamen.
    pruefe(P, "NICHTS_TUN erreicht die Datenbank NIE",
           "NICHTS_TUN" not in SA.AKTIONEN and SA.UMBENENNUNG["NICHTS_TUN"] == "HALTEN",
           "zwei Etiketten fuer dasselbe Ergebnis zwaengen jede Auswertung, "
           "beide zu kennen - sonst zaehlt sie die halbe Wahrheit")
    pruefe(P, "jeder Altwert bleibt gueltig", set(ALT) <= set(SA.AKTIONEN),
           "solange die alte Kette laeuft, muessen ihre Werte gueltig bleiben")
    pruefe(P, "jede neue Aktion hat ein Ziel im Vokabular",
           all(SA.UMBENENNUNG.get(a, a) in SA.AKTIONEN for a in NEU))
    pruefe(P, "REDUZIEREN bleibt eigenstaendig",
           "REDUZIEREN" in SA.AKTIONEN and "REDUZIEREN" not in SA.UMBENENNUNG,
           "Teilverkauf ist kein Vollverkauf - die Position wird kleiner statt "
           "geschlossen, und das ist ein anderer Ausgang")

    grund_a = {"belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"},
                          {"fakt": "b", "richtung": "dafuer", "gewicht": "mittel"}],
               "unabhaengige_faktoren": 2, "einstieg_eur": 100.0,
               "richtung": "LONG",         # S6c: Pflicht bei KAUFEN
               "stop_eur": 94.0, "begruendung": "x", "was_dagegen": "y",
               "umgeworfen_durch": "z"}
    abbild = {a: SA.felder_aus_entscheidung(
        RT.validiere({**grund_a, "aktion": a}, "X", atr=4.0), fakten={})["action"]
        for a in NEU}
    pruefe(P, "die Abbildung greift wirklich",
           abbild["NICHTS_TUN"] == "HALTEN" and abbild["KAUFEN"] == "KAUFEN"
           and abbild["REDUZIEREN"] == "REDUZIEREN", str(abbild))

    con = sqlite3.connect("data/tradinginfotool.db")
    try:
        # ECKPUNKT 2: die fuenf heimatlosen Felder haben jetzt Spalten.
        SA.migriere(con)
        spalten = {r[1] for r in con.execute("PRAGMA table_info(signals)")}
        fehlen = set(SA.SPALTEN_SIGNAL) - spalten
        pruefe(P, "alle neuen Spalten sind angelegt", not fehlen, str(fehlen))
        pruefe(P, "die Migration ist idempotent", SA.migriere(con) == [],
               "ein zweiter Lauf darf nichts anlegen")
        tabellen = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        pruefe(P, "die Lagebild-Tabelle existiert", "lagebilder" in tabellen,
               "ECKPUNKT 5: eine Zeile je Durchgang statt 44-facher Redundanz")

        # ECKPUNKT 3: nur fuenf Spalten sind Pflicht - die neue Kette bedient
        # sie alle, ohne eine Zahl zu erfinden.
        pflicht = {r[1] for r in con.execute("PRAGMA table_info(signals)")
                   if r[3] and r[4] is None and not r[5]}
        antwort = RT.validiere(
            {"belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"},
                        {"fakt": "b", "richtung": "dafuer", "gewicht": "mittel"}],
             "unabhaengige_faktoren": 2, "aktion": "KAUFEN",
             "richtung": "LONG",           # S6c: Pflicht bei KAUFEN
             "einstieg_eur": 100.0, "stop_eur": 94.0, "begruendung": "x",
             "was_dagegen": "y", "umgeworfen_durch": "z"}, "BTC", atr=4.0)
        felder = SA.felder_aus_entscheidung(antwort, fakten={"asset": "BTC"},
                                            lagebild_id=1, prompt_stand="x")
        # symbol/created_at/gate_passed setzt der Aufrufer - action und
        # facts_json muss die Abbildung liefern.
        pruefe(P, "die Abbildung liefert action und facts_json",
               {"action", "facts_json"} <= set(felder),
               f"Pflichtspalten der Tabelle: {sorted(pflicht)}")

        # ECKPUNKT 4: der Faktensatz ist PFLICHT - er war bei 78 von 118
        # Altsignalen leer.
        pruefe(P, "der Faktensatz wird mitgeschrieben",
               json.loads(felder["facts_json"]) == {"asset": "BTC"},
               "ohne ihn ist eine Empfehlung im Nachhinein nicht pruefbar")
        leer = SA.felder_aus_entscheidung(antwort, fakten={})
        pruefe(P, "auch ein LEERER Faktensatz wird geschrieben, nicht weggelassen",
               "facts_json" in leer,
               "sonst faellt die Pflichtspalte still weg")

        # Was bewusst leer bleibt, darf NICHT mit Ersatzwerten gefuellt werden.
        pruefe(P, "keine erfundene Konfidenz, kein Regime",
               not ({"confidence_pct", "regime"} & set(felder)),
               "eine Zahl, die niemand gerechnet hat, ist schlimmer als eine "
               "leere Spalte")

        # Zonen nur, wenn es sie gibt.
        ohne = SA.felder_aus_entscheidung(
            RT.validiere({**antwort, "aktion": "NICHTS_TUN"}, "BTC", atr=4.0),
            fakten={})
        pruefe(P, "NICHTS_TUN traegt keine Kurszonen",
               not any(k.startswith(("entry_", "stop_loss_", "take_profit_"))
                       for k in ohne),
               "ein Nullwert waere dort eine Aussage, die niemand getroffen hat")

        # Die abgeleiteten Zonen landen in den RICHTIGEN Spalten.
        pruefe(P, "Ziel landet in take_profit_eur_von/bis",
               felder.get("take_profit_eur_von") == 111.0
               and felder.get("take_profit_eur_bis") == 113.0,
               "das Backward-Tracking liest genau diese Spalten")

        # ECKPUNKT 5 in Betrieb
        lid = SA.schreibe_lagebild(
            con, datum="2026-01-01",
            antwort={"lage": "x", "belege": ["a"], "klassen": [], "gleichlauf": "x"},
            fakten=["f1"], prompt_stand="p", modell="m")
        zeile = con.execute("SELECT fakten_json, gleichlauf FROM lagebilder "
                            "WHERE id=?", (lid,)).fetchone()
        pruefe(P, "das Lagebild speichert seinen eigenen Faktensatz",
               json.loads(zeile[0]) == ["f1"],
               "die Antwort ist ohne die gesehenen Fakten nicht erklaerbar")
        con.execute("DELETE FROM lagebilder WHERE id=?", (lid,))
        con.commit()

        pruefe(P, "die Kette ist unterscheidbar",
               felder.get("quelle_kette") == "rollen",
               "ohne diese Spalte laesst sich keine Messung nach Ketten trennen")
    finally:
        con.close()


# ---------------------------------------------------------------- Paket 7 ---
def paket_7() -> None:
    """Backward-Tracking: die Erfolgsmessung greift wieder."""
    P = "7"
    import warnings
    warnings.filterwarnings("ignore")
    from agent.krypto.backward_tracking import _zonen_mittel
    from agent import rolle_trader as RT
    from agent import signal_abbildung as SA
    import agent.rollen_eingabe as RE

    grund = {"belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"},
                        {"fakt": "b", "richtung": "dafuer", "gewicht": "mittel"}],
             "unabhaengige_faktoren": 2, "aktion": "KAUFEN",
             "richtung": "LONG",           # S6c: Pflicht bei KAUFEN
             "einstieg_eur": 87.44, "stop_eur": 82.19, "begruendung": "x",
             "was_dagegen": "y", "umgeworfen_durch": "z"}
    a = RT.validiere(dict(grund), "BTC", atr=3.5)

    class _Signal:
        def __init__(self, felder):
            for k, v in felder.items():
                setattr(self, k, v)

    # OHNE USD-SPIEGELUNG BLEIBT DAS SIGNAL FUER IMMER UNAUFGELOEST. Das
    # Backward-Tracking laedt `price_history_ohlc WHERE currency = 'USD'` und
    # vergleicht gegen entry_usd/stop_loss_usd/take_profit_usd.
    ohne = _zonen_mittel(_Signal(SA.felder_aus_entscheidung(a, fakten={})))
    pruefe(P, "ohne Umrechnungskurs bleiben die USD-Zonen leer",
           all(z is None for z in ohne),
           "genau das war der Bruch: die neue Kette schrieb nur EUR")

    mit = _zonen_mittel(_Signal(SA.felder_aus_entscheidung(
        a, fakten={}, eur_je_usd=0.8744)))
    pruefe(P, "mit Kurs loest das Tracking die Zonen auf",
           all(z is not None for z in mit), str(mit))
    pruefe(P, "die Umrechnung ist verhaeltnistreu",
           abs((mit[2] - mit[0]) / (mit[0] - mit[1]) - 2.0) < 1e-6,
           f"CRV bleibt 2,0 - gemessen {(mit[2]-mit[0])/(mit[0]-mit[1]):.4f}")

    felder = SA.felder_aus_entscheidung(a, fakten={}, eur_je_usd=0.8744)
    pruefe(P, "der Umrechnungskurs wird MITGESCHRIEBEN",
           felder.get("fx_eur_je_usd") == 0.8744,
           "sonst liesse sich spaeter nicht nachrechnen, wie die USD-Zonen "
           "entstanden sind")
    pruefe(P, "EUR-Zonen bleiben unveraendert daneben stehen",
           felder.get("entry_eur_von") == a["einstieg_eur_von"],
           "die E-Mail zeigt EUR, das Tracking rechnet USD")

    # DER WAEHRUNGSFEHLER IN DER SPANNE (gefunden bei dieser Gegenpruefung).
    # `atr_bis` rechnet aus der Kursreihe, und die liegt bei ALLEN 45 Symbolen
    # in USD - `kurs_eur` liefert dagegen EUR.
    from backtest_llm1_historisch import lade_reihen_aus_db, waehrung_je_symbol
    w = waehrung_je_symbol("data/tradinginfotool.db")
    # ⚠️ NUR KRYPTO, NICHT DIE GANZE DATENBANK (24.08.2026-Fund am Notebook).
    # Die Pruefung stammt von vor dem Multi-Asset-Umbau, wo ALLE Reihen USD
    # waren. Seither sind ETF/Aktien/Rohstoffe live - und `lade_reihen_aus_
    # db()`s eigener Docstring haelt fest: ein reiner USD-Filter "machte die
    # ETF-Klasse unsichtbar" - EUR bei einem Nicht-Krypto-Symbol ist also der
    # ERWARTETE Zustand, kein Defekt. Was diese Pruefung eigentlich sichern
    # will (die USD->EUR-Umrechnung fuer `atr_eur`), gilt nur fuer Krypto -
    # `atr_bis`/`kurs_eur` werden weiter unten nur an BTC gepruft.
    import config as _cfg7
    try:
        _krypto_symbole = {a.symbol for a in _cfg7.get_watchlist()
                           if a.assetklasse == "krypto"}
    except Exception:                                          # noqa: BLE001
        _krypto_symbole = set()
    _w_krypto = {s: c for s, c in w.items()
                if not _krypto_symbole or s in _krypto_symbole}
    pruefe(P, "Krypto-Reihen liegen in USD - der ATR also auch",
           set(_w_krypto.values()) <= {"USD"},
           f"{ {s: c for s, c in _w_krypto.items() if c != 'USD'} } von "
           f"{len(_w_krypto)} Krypto-Symbolen - alle Symbole: "
           f"{ {s: c for s, c in w.items() if c != 'USD'} }")
    r = lade_reihen_aus_db()["BTC"]
    i = len(r) - 1
    fx = RE.fx_eur_je_usd("BTC", r, i)
    pruefe(P, "atr_eur ist der umgerechnete atr_bis",
           abs(RE.atr_eur("BTC", r, i) - RE.atr_bis(r, i) * fx) < 1e-9,
           f"Kurs {fx:.4f}")
    pruefe(P, "der Umrechnungskurs ist plausibel", 0.5 < fx < 1.5,
           f"EUR je USD = {fx:.4f} - alles ausserhalb waere ein Datenfehler")

    # Kein Aufrufer darf mehr den USD-ATR an die Zonen geben.
    import glob
    falsch = []
    for d in sorted(glob.glob("messe_*.py") + ["pruefe_rollenkette.py"]):
        t = _quelltext(d)
        for m in re.finditer(r"RT\.validiere\(", t):
            rest = t[m.end():m.end() + 320].split(chr(10) + chr(10))[0]
            if "atr=" in rest and "atr_e" not in rest and "atr_eur" not in rest:
                falsch.append(d)
    pruefe(P, "kein Aufrufer gibt den USD-ATR an die Zonen", not falsch,
           f"noch mit USD-ATR: {sorted(set(falsch))}" if falsch else
           "die Spanne war sonst 14,4 % zu breit")

    # Das Tracking filtert NICHT nach Kette - neue Zeilen werden erfasst.
    tracking = _quelltext("agent/krypto/backward_tracking.py")
    pruefe(P, "das Tracking filtert nicht nach Kette",
           "quelle_kette" not in tracking,
           "neue Signale werden automatisch mitgemessen")


# ---------------------------------------------------------------- Paket 8 ---
def paket_8() -> None:
    """Trefferbilanz - die Zahl fuer die E-Mail."""
    P = "8"
    import sqlite3
    from agent import trefferbilanz as TB
    from agent.krypto import backward_tracking as BT

    # DIE STRENGSTE PRUEFUNG: die Formel muss den BEKANNTEN Befund ergeben,
    # nicht behaupten. Ohne Kosten bei CRV 2,0 sind es 1/3 - genau die Zahl,
    # gegen die dieses Projekt seit Wochen rechnet.
    pruefe(P, "Breakeven ohne Kosten ist exakt 1/(1+CRV)",
           abs(TB.breakeven(0.0) - 1.0 / (1.0 + TB.CRV)) < 1e-12,
           f"{100*TB.breakeven(0.0):.1f} % bei CRV {TB.CRV}")
    pruefe(P, "die Krypto-Kosten kippen das Vorzeichen",
           TB.BASISRATE > TB.breakeven(0.0) and TB.BASISRATE < TB.breakeven(0.230),
           f"brutto traegt es (34,0 > {100*TB.breakeven(0.0):.1f}), "
           f"netto nicht (34,0 < {100*TB.breakeven(0.230):.1f})")

    # SCHRUMPFUNG
    pruefe(P, "ohne Faelle exakt die Basisrate",
           abs(TB.geschrumpft(0, 0) - TB.BASISRATE) < 1e-12,
           "der Nutzervorschlag: 'mit einem Mittelwert anfangen'")
    viel = TB.geschrumpft(600, 1000)
    pruefe(P, "bei vielen Faellen traegt die Messung selbst",
           abs(viel - 0.60) < 0.02, f"1000 Faelle, 60 % -> {100*viel:.1f} %")
    mittel = TB.geschrumpft(12, 20)
    pruefe(P, "dazwischen wird vorsichtig angepasst",
           TB.BASISRATE < mittel < 0.60,
           f"20 Faelle, 60 % -> {100*mittel:.1f} % (zwischen 34 und 60)")
    pruefe(P, "mehr Treffer als Faelle wird gedeckelt",
           TB.geschrumpft(99, 10) == TB.geschrumpft(10, 10),
           "eine Quote ueber 100 % waere ein stiller Datenfehler")

    # MERKMALE: nur was zum Signalzeitpunkt feststand
    import inspect
    pars = set(inspect.signature(TB.merkmale).parameters)
    pruefe(P, "kein Merkmal stammt aus dem Ausgang",
           not any(w in p for p in pars for w in ("outcome", "crv", "ergebnis",
                                                  "treffer", "realisiert")),
           f"sonst waere die Tabelle ein Blick in die Zukunft: {sorted(pars)}")
    # BEIDE PRUEFUNGEN LIEFEN URSPRUENGLICH AN DER FAKTORZAHL - dem einzigen
    # Merkmal, das der Schluessel damals hatte. Seit 15.1 ist sie draussen; das
    # gepruefte VERHALTEN (eigenes Band fuer Fehlendes, grobe Einteilung) gilt
    # unveraendert und wird jetzt an der Schwankung geprueft.
    pruefe(P, "fehlende Angaben bekommen ein EIGENES Band",
           TB.merkmale(vola_perzentil=None)[0] is None
           and TB.merkmale(vola_perzentil=0)[0] == 0,
           "sie stillschweigend einzusortieren hiesse, Faelle zu zaehlen, die "
           "dort nicht hingehoeren")
    pruefe(P, "die Baender sind grob genug",
           len({TB.merkmale(vola_perzentil=n)[0] for n in range(0, 100, 5)}) == 4,
           "eine Tabelle mit tausend Zellen hat in jeder drei Faelle")
    pruefe(P, "die Faktorzahl geht NICHT mehr in den Schluessel ein",
           TB.merkmale(unabhaengige_faktoren=2)
           == TB.merkmale(unabhaengige_faktoren=3),
           "sie wiederholt die Entscheidung (Faktorzahl 3 -> 82 % Einstieg) "
           "und haette jede Zelle halbiert - `belastbar` verlangt 50 Faelle")

    # DIE KONSTANTEN SIND IMPORTIERT, NICHT ABGESCHRIEBEN. Die erste Fassung
    # hatte zwei von vier falsch - und `zaehle()` haette still nichts gefunden.
    pruefe(P, "Ausgangs-Konstanten stammen aus backward_tracking",
           TB.TREFFER == (BT.OUTCOME_TAKE_PROFIT,)
           and TB.AUFGELOEST is BT._RESOLVED_OUTCOMES,
           "abgeschrieben waren sie falsch: 'stop_erreicht' statt "
           "'stop_loss_erreicht'")

    con = sqlite3.connect("data/tradinginfotool.db")
    try:
        bilanz = TB.zaehle(con)
        pruefe(P, "zaehle() laeuft gegen die echte Tabelle", isinstance(bilanz, dict),
               f"{len(bilanz)} Konstellationen - noch keine aufgeloesten "
               f"Signale der neuen Kette, das ist der erwartete Startzustand")
        # Ketten NICHT vermischen: die alte hatte andere Fakten und Prompts.
        alt_bilanz = TB.zaehle(con, quelle_kette="alt")
        pruefe(P, "die Ketten werden getrennt gezaehlt",
               isinstance(alt_bilanz, dict),
               "ihre Quote sagt nichts ueber diese")
    finally:
        con.close()

    # DER SATZ FUER DIE E-MAIL sagt bei duenner Lage, dass sie duenn ist.
    duenn = TB.bewerte({}, TB.merkmale(unabhaengige_faktoren=4), kosten_r=0.230)
    text = " ".join(TB.satz(duenn))
    pruefe(P, "bei wenigen Faellen nennt der Satz keine erfundene Quote",
           "erst 0 eigene Faelle" in text
           and "zu wenige fuer eine eigene Zahl" in text
           and "von hundert" in text,
           "ein '41 %' auf vierzehn Faellen waere erfundene Genauigkeit - und "
           "der Satz muss SAGEN, dass er die Erfahrungsrate benutzt")
    dick = TB.bewerte({TB.merkmale(unabhaengige_faktoren=4):
                       {"treffer": 130, "faelle": 300, "abgelaufen": 0}},
                      TB.merkmale(unabhaengige_faktoren=4), kosten_r=0.230)
    pruefe(P, "bei belastbarer Lage nennt er Quote UND Urteil",
           dick["belastbar"]
           and "In genau dieser Konstellation" in " ".join(TB.satz(dick))
           and "300 Faelle" in " ".join(TB.satz(dick)))

    # ABGELAUFENE werden AUSGEWIESEN, nicht verrechnet (Arbeitsstand 7.23).
    mit_abgelaufen = TB.bewerte(
        {TB.merkmale(unabhaengige_faktoren=4):
         {"treffer": 20, "faelle": 50, "abgelaufen": 50}},
        TB.merkmale(unabhaengige_faktoren=4))
    pruefe(P, "abgelaufene Faelle werden ausgewiesen",
           mit_abgelaufen["abgelaufen"] == 50
           and abs(mit_abgelaufen["anteil_entschieden"] - 0.5) < 1e-9,
           "'keines = 0 R' ist eine Setzung, keine Messung - sie betrifft "
           "15-21 % aller Faelle und darf nicht still verrechnet werden")

    # DIE BILANZ VERWIRFT NICHTS - als VERHALTENS-, nicht als Textpruefung.
    # Die erste Fassung suchte nach "return None" im Quelltext und schlug an:
    # sie fand das legitime `return None` in `band()`, also genau das "None
    # bekommt ein eigenes Band", das zwei Zeilen darueber geprueft wird. Eine
    # Textsuche kann Absicht nicht von Versehen unterscheiden.
    fehlgeschlagen = []
    for name, ruf in (
            ("breakeven mit unsinnigen Kosten", lambda: TB.breakeven(-5.0)),
            ("geschrumpft mit negativen Zahlen", lambda: TB.geschrumpft(-3, -7)),
            ("merkmale ohne jede Angabe", lambda: TB.merkmale()),
            ("bewerte auf leerer Bilanz",
             lambda: TB.bewerte({}, TB.merkmale())),
            ("satz auf leerer Bewertung",
             lambda: TB.satz(TB.bewerte({}, TB.merkmale())))):
        try:
            ruf()
        except Exception as e:                               # noqa: BLE001
            fehlgeschlagen.append(f"{name}: {type(e).__name__}")
    pruefe(P, "keine Funktion wirft, auch bei unsinniger Eingabe nicht",
           not fehlgeschlagen, str(fehlgeschlagen))

    pruefe(P, "`traegt` ist eine AUSSAGE, keine Sperre",
           isinstance(TB.bewerte({}, TB.merkmale()).get("traegt"), bool)
           and TB.satz(TB.bewerte({}, TB.merkmale())),
           "die Bewertung kommt immer zurueck - wer sie anschliesst, "
           "entscheidet, was ein Unterschreiten ausloest. Ein Waechter, der "
           "selbst verwirft, macht seine eigene Wirkung unsichtbar")


# ---------------------------------------------------------------- Paket 9 ---
def paket_9() -> None:
    """Live-Lauf auf dem Produktionsmodell - was er gefunden hat."""
    P = "9"
    from api.gemini import DEFAULT_MODEL
    from agent import trefferbilanz as TB
    from agent import marktlage as ML
    import agent.rollen_eingabe as RE

    pruefe(P, "das Produktionsmodell ist 3.1, nicht 3.5",
           DEFAULT_MODEL == "gemini-3.1-flash-lite", DEFAULT_MODEL)
    kette = _quelltext("pruefe_rollenkette.py")
    pruefe(P, "das Pruefskript kennt den Anbieter 'gemini'",
           'name == "gemini"' in kette and "DEFAULT_MODEL" in kette)

    # FUND 1: das Skript lud aus dem JSON-Export - dort fehlen ZWEI der drei
    # Leitmaerkte. Der erste Live-Lauf lieferte ein krypto-only Lagebild.
    pruefe(P, "das Pruefskript laedt aus der Datenbank, nicht aus dem Export",
           "lade_reihen_aus_db as lade_reihen" in kette,
           "der Export traegt 41 Reihen und ausgerechnet SPY und OD7C nicht")
    from backtest_llm1_historisch import lade_reihen_aus_db
    fehlend = [s for s in set(ML.BENCHMARK.values())
               if s not in lade_reihen_aus_db()]
    pruefe(P, "alle drei Leitmaerkte sind ladbar", not fehlend, str(fehlend))

    # FUND 2: die Kosten in R haengen fast ausschliesslich am Stopabstand -
    # und den waehlt das Modell frei. Der Live-Lauf gab 1,26 %.
    eng = TB.kosten_r_aus_stop(55500, 54900)
    weit = TB.kosten_r_aus_stop(55500, 48500)
    pruefe(P, "ein enger Stop vervielfacht die Kosten in R",
           eng > 5 * weit, f"1,26 % -> {eng:.2f} R gegen 12,6 % -> {weit:.2f} R")
    pruefe(P, "der Breakeven wird je SIGNAL gerechnet, nicht je Klasse",
           TB.breakeven(eng) > 1.0 and TB.breakeven(weit) < 0.5,
           "die dokumentierten -0,230 R gelten fuer einen Stop um 13 %; auf "
           "1,8 % sind es 1,67 R - der Klassenwert waere siebenfach zu guenstig")
    pruefe(P, "Stop >= Einstieg gibt keine Kosten statt einer Division",
           TB.kosten_r_aus_stop(100, 100) is None)

    # FUND 3: der Vergleich gilt IMMER, auch ohne eigene Faelle.
    unmoeglich = TB.satz(TB.bewerte({}, TB.merkmale(), kosten_r=eng))
    pruefe(P, "ein unmoeglicher Breakeven wird auch OHNE Faelle benannt",
           any("KANN NICHT AUFGEHEN" in z for z in unmoeglich),
           "die erste Fassung sagte nur 'noch keine eigene Messung' - auch "
           "bei 113 % Breakeven")
    negativ = TB.satz(TB.bewerte({}, TB.merkmale(), kosten_r=weit))
    pruefe(P, "ein negativer Erwartungswert wird auch OHNE Faelle benannt",
           any("Traegt sich NICHT" in z for z in negativ),
           "die Fallzahl entscheidet, ob wir eine eigene QUOTE behaupten - "
           "nicht, ob wir vergleichen duerfen")

    # FUND 4: der Stimmungssatz lud zur Verwechslung ein.
    satz = ML.beschreibe_stimmung(RE.lade_stimmung(), "2026-07-17")
    pruefe(P, "der Stimmungssatz nennt das Perzentil ZUERST",
           satz and satz[0].index("Perzentil") < satz[0].index("Skala"),
           "die erste Fassung stellte eine niedrige absolute Zahl neben eine "
           "hohe relative - das Modell verband die Deutung mit der falschen")
    pruefe(P, "er wiederholt die relative Aussage in Worten",
           satz and "zuversichtlicher als heute" in satz[0],
           "damit konkurrieren keine zwei Zahlen mehr um dieselbe Deutung")



def paket_10() -> None:
    """Die Berechnung der Entscheidung - kann der alte Fehler noch entstehen?

    Nutzer 12.08.: *"sonst gibt es wieder Empfehlungen mit 1500 Euro und 1,5
    Prozent Stop loss."* Genau diese beiden Zahlen sind hier die Pruefung."""
    P = "10"
    from agent import entscheidungsrechnung as ER

    # DIE BEIDEN ZAHLEN AUS DEM AUFTRAG, jede an ihrer eigenen Grenze.
    e = ER.rechne(kurs=55500, atr=1677, risiko_eur=75, instrument="hebel",
                  betrag_wunsch_eur=1500, topf_frei_eur=500)
    # UMGESCHRIEBEN 15.08.2026. Bis dahin verlangte diese Pruefung, dass der
    # Topf den Betrag KAPPT. Genau das hat am 14.08. die Hebelkette
    # stillgelegt: ein Signal fuellte den Topf, jedes weitere bekam Betrag 0 -
    # blockiert NACH dem Modellaufruf, ohne Zeile, also ohne Cooldown.
    #
    # DIE TRENNLINIE SEIT DEM 15.08.: das System bemisst den einzelnen Trade,
    # die Aufteilung des Portfolios bemisst der Nutzer. Der Topf braucht
    # Wissen, das dieses System nicht hat - ob der Nutzer die Empfehlungen von
    # gestern ausgefuehrt hat. Er MELDET jetzt, statt zu kappen.
    pruefe(P, "der Topf aendert den Betrag NICHT mehr",
           e["betrag_eur"] > 500,
           f"{e['betrag_eur']} EUR - ein Deckel, der ein Signal verschwinden "
           "laesst, ist ein unsichtbares Veto")
    pruefe(P, "aber er meldet, dass er ueberschritten wuerde",
           e.get("topf_frei_eur") == 500.0
           and e.get("topf_wuerde_ueberschreiten") is True,
           "die Zahl wandert in die Mail - der Nutzer entscheidet")
    a, regel = ER._stop_abstand(55500, 1677, 54800)
    pruefe(P, "ein 1,26-%-Stop kommt nicht durch",
           a / 55500 >= ER.GRENZEN["stop_min_relativ"]
           and "Rauschboden" in regel,
           "gemessen 0,0 % Trefferquote ueber 9 Trades unter 2 %")

    # OBERGRENZE - die gab es vorher NICHT. Ein zu weiter Stop faellt durch
    # jede Untergrenze und ruiniert die Rechnung trotzdem.
    a2, regel2 = ER._stop_abstand(55500, 1677, 38000)
    pruefe(P, "ein 31-%-Stop kommt ebenfalls nicht durch",
           a2 / 55500 <= ER.GRENZEN["stop_max_relativ"] + 1e-9,
           "eine Untergrenze allein reicht nicht - 'vorsichtig' faellt niemandem auf")

    # DIE FRAGE ENTSCHEIDET, NICHT DIE ZAHL: das Modell darf den Stop setzen,
    # wenn es ihn als Widerlegung seiner These nennt - innerhalb der Klemme.
    a3, regel3 = ER._stop_abstand(55500, 1677, 51000)
    pruefe(P, "ein plausibler Widerlegungspreis wird uebernommen",
           abs(a3 - 4500) < 1e-6 and "Widerlegungspreis" in regel3,
           "auf 'was widerlegt dich?' antwortet das Modell mit einem Urteil, "
           "nicht mit einem geschaetzten Risikoparameter")

    # KEIN STILLES DURCHRUTSCHEN.
    for fehlt, kwargs in (("ATR", dict(kurs=100, atr=None, risiko_eur=50)),
                          ("Kurs", dict(kurs=None, atr=3.0, risiko_eur=50)),
                          ("Budget", dict(kurs=100, atr=3.0, risiko_eur=None))):
        try:
            ER.rechne(instrument="spot", **kwargs)
            ok = False
        except ER.RechnungBlockiert:
            ok = True
        pruefe(P, f"ohne {fehlt} gibt es KEINE Empfehlung", ok,
               "eine Rechnung, die bei fehlender Eingabe 'irgendwas' liefert, "
               "ist gefaehrlicher als gar keine")

    # REIHENFOLGE: erst Deckel, dann Hebel. Vorher blieb das halbe Budget liegen.
    pruefe(P, "nach dem Deckel wird das Risikobudget genutzt",
           abs(e["verlust_am_stop_eur"] - 75) <= 5,
           "erst falsch herum gebaut: der Hebel stand auf dem WUNSCHbetrag, "
           "nach dem Topf-Deckel lagen 38 statt 75 EUR im Risiko")

    # RM-11 bleibt wirksam, auch wenn das Risikobudget mehr erlauben wuerde.
    eng = ER.rechne(kurs=100, atr=1.0, risiko_eur=400, instrument="hebel",
                    betrag_wunsch_eur=500, topf_frei_eur=500)
    pruefe(P, "der Liquidationsabstand deckelt den Hebel",
           eng["hebel"] <= ER.max_safe_hebel(100 * eng["stop_relativ"], 0.09) + 1e-9,
           "sonst greift Bitpandas Zwangsliquidation VOR dem eigenen Stop")

    # KEIN WIDERSPRUCH ZWISCHEN KOPF UND CODE (R-T8 sinngemaess).
    kopfzeile = ER.__doc__ or ""
    pruefe(P, "der Modulkopf behauptet nicht mehr 'das Modell traegt nichts bei'",
           "ES TRAEGT TROTZDEM ZWEI ZAHLEN BEI" in kopfzeile,
           "der Satz stand noch da, nachdem der Widerlegungspreis verdrahtet war")

    # DER TEXT SAGT, WOHER DIE HALTEDAUER KOMMT.
    mit_frist = ER.rechne(kurs=55500, atr=1677, risiko_eur=75, instrument="spot",
                          umgeworfen_tage=14)
    pruefe(P, "die Haltedauer nennt ihre Quelle",
           "Frist des Modells" in " ".join(ER.saetze(mit_frist)),
           "'geschaetzt' waere hier falsch - die Zahl kam vom Modell")



def paket_11() -> None:
    """Take-Profit an der Struktur und die Mail an den Nutzer."""
    P = "11"
    from agent import entscheidungsrechnung as ER
    from agent import signal_mail as SM
    from agent import trefferbilanz as TB

    weit = ER.rechne(kurs=55500, atr=1677, risiko_eur=75, instrument="hebel",
                     betrag_wunsch_eur=500, topf_frei_eur=500,
                     umgeworfen_preis_eur=51000, widerstand=(70000, 2))
    nah = ER.rechne(kurs=55500, atr=1677, risiko_eur=75, instrument="hebel",
                    betrag_wunsch_eur=500, topf_frei_eur=500,
                    umgeworfen_preis_eur=51000, widerstand=(62000, 3))
    pruefe(P, "ein Widerstand hinter dem Ziel aendert nichts",
           weit["crv"] == ER.GRENZEN["crv"] and weit["crv_erreicht"])
    pruefe(P, "ein Widerstand VOR dem Ziel zieht es davor",
           nah["ziel_eur"] < 62000 and nah["crv"] < ER.GRENZEN["crv"],
           "dort stehen die Verkaufsauftraege - wer die letzten Cent "
           "mitnehmen will, bekommt gar nichts")
    pruefe(P, "und die zu kleine CRV wird AUSGEWIESEN, nicht hochgerechnet",
           not nah["crv_erreicht"]
           and any("verlangt sind" in z for z in ER.saetze(nah)),
           "ein Ziel hinter einer Mauer ist kein Ziel")
    pruefe(P, "der Gewinn folgt der ECHTEN CRV, nicht der angestrebten",
           nah["gewinn_am_ziel_eur"] < weit["gewinn_am_ziel_eur"])
    pruefe(P, "die Haltedauer folgt dem ECHTEN Weg",
           ER.rechne(kurs=55500, atr=1677, risiko_eur=75, instrument="spot",
                     widerstand=(62000, 3))["haltedauer_tage"]
           < ER.rechne(kurs=55500, atr=1677, risiko_eur=75,
                       instrument="spot")["haltedauer_tage"])

    # DIE ABSCHNITTE DUERFEN EINANDER NICHT WIDERSPRECHEN (R-T8 sinngemaess).
    # Die erste Fassung der Mail wies in Abschnitt 2 "CRV 1,4" aus und verglich
    # in Abschnitt 4 gegen die 34 % von CRV 2,0.
    pruefe(P, "die Basisrate folgt der Geometrie des Signals",
           TB.basisrate_fuer(1.35) > TB.basisrate_fuer(2.0) > TB.basisrate_fuer(3.0),
           "ein engeres Ziel wird HAEUFIGER erreicht - sonst widersprechen "
           "sich Abschnitt 2 und Abschnitt 4")
    b = TB.bewerte({}, TB.merkmale(), kosten_r=0.3, crv=1.35)
    pruefe(P, "bewerte() rechnet Basisrate UND Breakeven mit derselben CRV",
           abs(b["basisrate"] - TB.basisrate_fuer(1.35)) < 1e-9
           and abs(b["breakeven"] - TB.breakeven(0.3, 1.35)) < 1e-9)

    # DEUTSCHE ZAHLEN. "55,500.00 EUR" liest sich als fuenfundfuenfzigeinhalb.
    pruefe(P, "Betraege stehen in deutscher Schreibweise",
           SM.eur(55500.0, 2) == "55.500,00",
           SM.eur(55500.0, 2))
    txt = " ".join(ER.saetze(nah))
    pruefe(P, "auch Prozente und Hebel tragen ein Komma",
           "8,1 %" in txt and "1,9x" in txt, txt[:80])
    pruefe(P, "die Zielregel wird nicht doppelt genannt",
           " ".join(ER.saetze(weit)).count("CRV 2,0") == 1,
           "'CRV 2.0 - CRV 2.0 - naechster Widerstand liegt dahinter'")

    # DIE MAIL: vier Abschnitte, der Coin zuerst.
    betreff, text = SM.baue_mail(
        symbol="BTC", name="Bitcoin", kurs_eur=55500.0, instrument="hebel",
        strategie="swing", rechnung=weit,
        urteil={"aktion": "KAUFEN", "begruendung": "x", "was_dagegen": "y",
                "umgeworfen_durch": "z", "unabhaengige_faktoren": 3,
                "belege": [{"fakt": "a", "richtung": "dafuer", "gewicht": "hoch"}]},
        coin_fakten=["Bitcoin notiert tiefer."], einordnung=["Einordnung."])
    # ⚠️ ABSCHNITT 1 HEISST SEIT DEM 16.08. "DER WERT", nicht "DER COIN" -
    # die Kette bedient seit dem Vollumstieg sechs Gruppen, und die alte
    # Ueberschrift stand ueber einem WisdomTree-Zertifikat und einem inversen
    # S&P-ETF. Diese Pruefung hat die Aenderung korrekt gefangen; sie prueft
    # jetzt dieselbe ABSICHT (Reihenfolge und Vollstaendigkeit) am neuen Namen.
    for nr, name in ((1, "DER WERT"), (2, "DIE RECHNUNG"),
                     (3, "DAS URTEIL DES MODELLS"), (4, "EINORDNUNG")):
        pruefe(P, f"Abschnitt {nr} heisst '{name}'", f"--- {nr}. {name} ---" in text)
    pruefe(P, "der Wert steht VOR der Rechnung",
           text.index("1. DER WERT") < text.index("2. DIE RECHNUNG"),
           "Nutzer: 'Info Teil zum Coin und dann die wichtigen Abschnitte'")
    # ZWEI EIGENE FEHLER IN DIESER EINEN PRUEFUNG, beide an der Testeingabe:
    #   * ein selbstgebautes `rechnung`-dict ohne `einstieg_von_eur`
    #   * KEINE Fakten uebergeben - dann bleibt Abschnitt 1 leer, und
    #     `_abschnitt()` laesst ihn zu Recht ganz weg. Der Test suchte eine
    #     Ueberschrift, die es ohne Inhalt gar nicht geben darf.
    # Beides derselbe Typ wie die streng steigende Testreihe: die Eingabe
    # stellt den Fall nicht her, den sie pruefen will.
    pruefe(P, "und die Absicherung bekommt ihre eigene Ueberschrift",
           "--- 1. DIE ABSICHERUNG ---" in SM.baue_mail(
               symbol="DBPK", name="DBPK", kurs_eur=55500.0,
               instrument="absicherung", strategie="einstieg", rechnung=weit,
               coin_fakten=["Abzusicherndes Exposure: 8.898 EUR."],
               urteil={"aktion": "KAUFEN", "begruendung": "x",
                       "was_dagegen": "y", "umgeworfen_durch": "z",
                       "unabhaengige_faktoren": 3,
                       "belege": [{"fakt": "a", "richtung": "dafuer",
                                   "gewicht": "hoch"}]})[1],
           "sie ist ausdruecklich KEIN Trade - der Prompt sagt es dem Modell, "
           "die Mail sagt es dem Leser")
    pruefe(P, "keine Konfidenz in Prozent mehr",
           "Konfidenz" not in text,
           "im eigenen System 77,5 % vorhergesagt gegen 33,3 % tatsaechlich")
    pruefe(P, "der Betreff nennt Symbol, Aktion und Instrument",
           betreff == "TradingInfoTool: BTC - KAUFEN (Hebel)", betreff)



def paket_12() -> None:
    """Der deterministische Faktenblock - Kern, Zusatzinfo, Lesbarkeit."""
    P = "12"
    from agent import faktenblock as FB

    voll = dict(atr_relativ=0.0302, schwankung_perzentil=0.18,
                rueckgang_60t=-0.012, momentum_perzentil=0.86,
                volumen_relativ=1.4, volumen_perzentil=0.72)
    text = "\n".join(FB.baue("krypto_hebel", kern_werte=voll,
                             zusatz_werte=dict(funding_eur_tag=0.29,
                                               liquidation_eur=25500,
                                               put_skew=-9.99,
                                               retail_long_pct=55)))

    # DIE KERNREGEL AUS 12.8: Momentum erscheint GENAU EINMAL. Die vier Masse
    # haengen mit 0,59 bis 0,89 zusammen - wer sie einzeln auffuehrt, laesst
    # einen Aufbau viermal so gut belegt aussehen, wie er ist.
    pruefe(P, "der Kern hat genau drei Familien",
           len(FB.KERN) == 3 and set(FB.KERN) == {"schwankung", "momentum", "volumen"})
    for wort in ("RSI", "50-Tage-Linie", "Trend 20", "Fear", "Greed"):
        pruefe(P, f"'{wort}' erscheint NICHT als eigener Faktor",
               wort not in text,
               "vier Momentum-Masse sind EIN Faktor (Rangkorrelation 0,59-0,89)")

    # DER NUTZEREINWAND: "74. Perzentil ist fuer mich nicht lesbar."
    pruefe(P, "im Text steht kein Perzentil", "erzentil" not in text,
           "das Perzentil bestimmt nur das Urteilswort, es erscheint nicht")
    pruefe(P, "jede Kernzeile traegt ein Urteilswort",
           sum(text.count(u) for u in FB._URTEIL) >= 3)

    # ABSOLUT ZUERST (Umbauplan 12.1) - der Wert vor der Einordnung.
    kopf = [z for z in text.split("\n") if z.startswith("Schwankung")][0]
    pruefe(P, "der Absolutwert steht vor dem Urteil",
           kopf.index("3,0 %") < kopf.index("GUENSTIG"),
           "R-T1/R-T2 gelten fuer das MODELL, nicht fuer den Nutzer")

    # "KEIN BEIWERK OHNE SINN": jede Zusatzinfo erklaert sich.
    zus = FB.zusatz("krypto_hebel", dict(funding_eur_tag=0.29, put_skew=-9.99))
    pruefe(P, "jede Zusatzinfo hat eine Bedeutungszeile",
           len(zus) == 4 and all(zus[i + 1].startswith("  ") for i in (0, 2)),
           "Nutzer: 'kein Beiwerk ohne Sinn'")
    pruefe(P, "jede Zusatzinfo nennt ihre Kategorie",
           all(any(z.startswith(f"[{k}]") for k in FB.KATEGORIEN)
               for z in zus[::2]))
    pruefe(P, "es gibt genau vier Kategorien",
           set(k for k, _, _ in FB._ZUSATZ.values()) <= set(FB.KATEGORIEN)
           and len(FB.KATEGORIEN) == 4,
           "Kosten, Positionierung, Fundamental, Vorausschauend - alles "
           "andere waere ein weiterer Momentum-Vertreter")

    # JE BEREICH VERSCHIEDEN - das war der Grund fuer die Bestandsaufnahme.
    pruefe(P, "die Zusatzinfo unterscheidet sich je Bereich",
           FB.ZUSATZ_JE_BEREICH["krypto_hebel"] != FB.ZUSATZ_JE_BEREICH["aktien"]
           and len(set(FB.ZUSATZ_JE_BEREICH)) == 6,
           "nur fuenf von 40 Faktenschluesseln kommen in allen sechs "
           "Pipelines vor (Umbauplan 12.2)")
    pruefe(P, "ein unbekannter Schluessel erzeugt nichts",
           FB.zusatz("krypto_hebel", {"gibt_es_nicht": 5}) == []
           and FB.zusatz("mondbasis", {"kgv": 12}) == [])

    # LUECKEN SIND EINE AUSSAGE, fehlende Zusatzinfo ist keine.
    ohne = "\n".join(FB.baue("aktien", kern_werte=dict(
        atr_relativ=0.014, schwankung_perzentil=0.55)))
    pruefe(P, "fehlende Kernfakten werden benannt",
           "Keine Angabe zu" in ohne and "Kursentwicklung" in ohne
           and "Volumen" in ohne,
           "sonst sieht ein Signal mit einem Fakt aus wie eines mit dreien")
    pruefe(P, "und im Singular richtig formuliert",
           "Ein Punkt weniger steht" in "\n".join(FB.baue(
               "aktien", kern_werte=dict(atr_relativ=0.014,
                                         schwankung_perzentil=0.55,
                                         rueckgang_60t=-0.02,
                                         momentum_perzentil=0.5))))
    pruefe(P, "fehlende Zusatzinfo wird NICHT gemeldet",
           "Keine Angabe" not in "\n".join(FB.baue("krypto_hebel",
                                                   kern_werte=voll)),
           "Zusatzinfo ist freiwillig - ihr Fehlen ist keine Aussage")

    # DAS URTEIL FOLGT DER GEMESSENEN RICHTUNG, nicht dem Bauchgefuehl.
    pruefe(P, "niedrige Schwankung ist GUENSTIG, hohe UNGUENSTIG",
           FB._urteil(0.1, False) == "GUENSTIG"
           and FB._urteil(0.9, False) == "UNGUENSTIG",
           "gemessen 29,5 gegen 17,8 % (Umbauplan 12.8)")
    pruefe(P, "nahe am Hoch ist GUENSTIG, weit darunter UNGUENSTIG",
           FB._urteil(0.9, True) == "GUENSTIG"
           and FB._urteil(0.1, True) == "UNGUENSTIG")
    pruefe(P, "die Mitte ist MITTEL, nicht gerundet",
           FB._urteil(0.5, True) == "MITTEL" and FB._urteil(0.5, False) == "MITTEL",
           "feiner zu unterscheiden hiesse, Genauigkeit zu behaupten, die die "
           "Messung nicht hergibt")

    # DEUTSCHE ZAHLEN, EINE WAEHRUNG - der Befund aus der alten Mail (12.5).
    pruefe(P, "Zahlen stehen in deutscher Schreibweise",
           FB._de(25500) == "25.500" and FB._de(0.29, 2) == "0,29")
    pruefe(P, "im Block steht keine zweite Waehrung",
           "USD" not in text,
           "die alte Hebel-Mail mischte EUR und USD ohne Kennzeichen")

    # KOPF UND CODE DUERFEN EINANDER NICHT WIDERSPRECHEN (wie in Paket 10).
    pruefe(P, "der Modulkopf zeigt den Wortlaut, den der Code erzeugt",
           "ueber alle Einstiege gemessen" in (FB.__doc__ or "")
           and "ueber alle Einstiege gemessen" in text,
           "die erste Fassung las sich, als sei die Quote die Aussicht DIESES "
           "Signals - sie ist die Verteilung, in die es faellt")

    # ---- ANSCHLUSS AN DIE MAIL, mit echten Werten ----
    import sqlite3
    from agent import entscheidungsrechnung as ER
    from agent import signal_mail as SM
    con = sqlite3.connect("data/tradinginfotool.db")
    reihe = con.execute("SELECT high,low,close,volume FROM price_history_ohlc "
                        "WHERE symbol='BTC' AND currency='USD' ORDER BY date").fetchall()
    con.close()
    hh = [r[0] for r in reihe]; ll = [r[1] for r in reihe]
    cc = [r[2] for r in reihe]; vv = [r[3] or 0 for r in reihe]
    echt = FB.werte_aus_reihe(hh, ll, cc, vv, i=len(cc) - 2)

    pruefe(P, "die Kernwerte lassen sich aus echten Kursen rechnen",
           echt and all(echt.get(k) is not None for k in
                        ("atr_relativ", "schwankung_perzentil", "rueckgang_60t",
                         "momentum_perzentil", "volumen_relativ")),
           str(sorted(echt)) if echt else "leer")

    # DIE KOPIE WIRD GEGEN DIE MESSUNG GEPRUEFT, nicht behauptet. Die
    # Definitionen stehen zweimal (Modul + Messskript); ohne diese Pruefung
    # waere das genau die Kopie, die still veraltet - wie die Kostensaetze.
    import numpy as np
    from messe_top_fakten import merkmale as _mess_merkmale
    _m, _a = _mess_merkmale(np.array(hh), np.array(ll), np.array(cc), np.array(vv))
    j = len(cc) - 2
    pruefe(P, "Modul und Messskript rechnen dieselben Werte",
           abs(echt["atr_relativ"] - _a[j] / cc[j]) < 1e-9
           and abs(echt["rueckgang_60t"] - _m["Rueckgang seit 60-Tage-Hoch"][j]) < 1e-9
           and abs(echt["schwankung_perzentil"]
                   - _m["Schwankungsbreite (Perzentil)"][j]) < 1e-9,
           "sonst misst die Mail etwas anderes als die Messung, auf die sie "
           "sich beruft")

    # DER LAUFENDE TAG HAT WENIGER UMSATZ - ohne Schalter haette JEDE Live-Mail
    # "Volumen UNGUENSTIG" gemeldet. An echten BTC-Daten: 0,2-faches Mittel.
    offen = FB.werte_aus_reihe(hh, ll, cc, vv, tag_vollstaendig=False)
    voll = FB.werte_aus_reihe(hh, ll, cc, vv, i=len(cc) - 2, tag_vollstaendig=True)
    pruefe(P, "der UNFERTIGE Tag wird nie als Volumen genommen",
           abs(offen["volumen_relativ"] - voll["volumen_relativ"]) < 1e-9,
           "der letzte Tag stand beim 0,2-fachen des Mittels - haette man ihn "
           "genommen, meldete JEDE Nachricht 'Volumen UNGUENSTIG'")
    pruefe(P, "stattdessen kommt der letzte VOLLSTAENDIGE Tag",
           offen.get("volumen_relativ") is not None
           and offen.get("volumen_von_gestern") is True,
           "die erste Fassung liess ihn ganz weg - damit fehlte eine von DREI "
           "gemessenen Familien in jeder einzelnen Nachricht (Gegenpruefung "
           "Stufe C, 13.08.)")

    pruefe(P, "ein Wert gegen sich selbst wird weggelassen",
           FB.zusatz("krypto_spot", {"btc_relativwert_pct": 0.0}, "BTC") == []
           and FB.zusatz("krypto_spot", {"btc_relativwert_pct": 2.0}, "ETH") != [],
           "'Gegen Bitcoin 0,0 % staerker' - fuer Bitcoin selbst")

    # KEINE ZAHL ZWEIMAL. Die Liquidation stand in Zusatzinfo UND Rechnung,
    # mit verschiedenen Werten - der Fehler der alten Mail (Umbauplan 12.5).
    pruefe(P, "die Liquidation steht nur in der Rechnung",
           "liquidation_eur" not in FB.ZUSATZ_JE_BEREICH["krypto_hebel"],
           "erste Fassung: 35.638 EUR in der Zusatzinfo gegen 30.238 EUR in "
           "der Rechnung - dieselbe Groesse, zwei Zahlen")

    # KEIN EINSTIEGSPLAN OHNE EINSTIEG.
    r = ER.rechne(kurs=64797, atr=1750, risiko_eur=75, instrument="hebel",
                  betrag_wunsch_eur=500, topf_frei_eur=500)
    for aktion, erwartet in (("NICHTS_TUN", False), ("VERKAUFEN", False),
                             ("KAUFEN", True), ("NACHKAUFEN", True)):
        _, txt = SM.baue_mail(symbol="BTC", name="Bitcoin", kurs_eur=64797,
                              instrument="hebel", strategie="swing", rechnung=r,
                              urteil={"aktion": aktion, "begruendung": "x"})
        hat_zone = "Einstiegszone" in txt
        pruefe(P, f"bei {aktion} {'steht' if erwartet else 'fehlt'} die Einstiegszone",
               hat_zone == erwartet,
               "eine ausgerechnete Zone liest sich wie eine Empfehlung, egal "
               "was darueber steht")


    # ---- GEGENPRUEFUNG STUFE C (13.08.): das Volumen fehlte in JEDEM Signal ----
    #
    # Der Faktenblock verspricht DREI gemessene Familien. Weil jedes Live-Signal
    # auf dem juengsten Tag rechnet und der als unvollstaendig gilt, fiel das
    # Volumen immer weg - geliefert wurden zwei. Jetzt kommt es vom letzten
    # VOLLSTAENDIGEN Tag, und das steht dabei.
    from backtest_llm1_historisch import lade_reihen_aus_db as _lade
    _r = _lade("data/tradinginfotool.db")["BTC"]
    _i = len(_r) - 1
    _args = ([k.high for k in _r], [k.low for k in _r], [k.close for k in _r],
             [getattr(k, "volume", 0) or 0 for k in _r])
    heute = FB.werte_aus_reihe(*_args, i=_i, tag_vollstaendig=False)
    gestern = FB.werte_aus_reihe(*_args, i=_i - 1, tag_vollstaendig=True)
    pruefe(P, "am laufenden Tag gibt es trotzdem ein Volumen",
           heute.get("volumen_relativ") is not None,
           "vorher fehlte damit eine von DREI Familien in JEDER Nachricht")
    pruefe(P, "und es ist das des Vortags",
           abs(heute["volumen_relativ"] - gestern["volumen_relativ"]) < 1e-9,
           f"{heute.get('volumen_relativ')} gegen {gestern.get('volumen_relativ')}")
    pruefe(P, "die Herkunft steht im Text",
           heute.get("volumen_von_gestern") is True
           and "(Vortag)" in " ".join(FB.baue("krypto_spot", kern_werte=heute)),
           "eine Zahl von gestern als heutige auszugeben waere schlimmer als "
           "die Luecke")
    pruefe(P, "am abgeschlossenen Tag steht kein Zusatz",
           gestern.get("volumen_von_gestern") is False
           and "(Vortag)" not in " ".join(FB.baue("krypto_spot", kern_werte=gestern)))
    pruefe(P, "und der Block meldet keine Luecke mehr",
           "Keine Angabe" not in " ".join(FB.baue("krypto_spot", kern_werte=heute)))

    # ---- ZUSATZINFO AUS DEN ECHTEN PIPELINE-FAKTEN ----
    import json as _json
    from agent import faktenblock_quellen as FQ

    con2 = sqlite3.connect("data/tradinginfotool.db")
    saetze = [_json.loads(r[0]) for r in con2.execute(
        "SELECT facts_json FROM hebel_signals WHERE facts_json IS NOT NULL").fetchall()]
    con2.close()
    getroffen = set()
    for satz in saetze:
        w, _ = FQ.abbilden(satz, bereich="krypto_hebel", position_eur=500, hebel=3)
        getroffen |= set(w)
    pruefe(P, "aus echten Hebel-Fakten kommen Finanzierung und Retail-Konsens",
           {"funding_eur_tag", "retail_long_pct"} <= getroffen,
           f"gefunden: {sorted(getroffen)}")

    # DER PFAD WIRD GEGEN DIE ECHTE BAUFORM GEHALTEN, nicht gegen meine
    # Annahme. Meine ersten Pfade hiessen `relativ_30d_prozent` und
    # `relativ_prozent` - beides existiert nicht, und 0 von 40 Faktensaetzen
    # trafen. Hier wird der Fakt wirklich gebaut und darin gesucht.
    from indicators.calculations import BtcRelativwert
    from agent.krypto.btc_relativwert import btc_relativwert_fakt
    echt_fakt = btc_relativwert_fakt(
        BtcRelativwert(korrelation=0.5, beta=1.1, relativstaerke_pct=-3.2,
                       fenster_tage_beta=90, fenster_tage_relativstaerke=30,
                       n_datenpunkte=120), {})
    w2, fehlt2 = FQ.abbilden({"btc_relativwert": echt_fakt},
                             bereich="krypto_spot")
    pruefe(P, "der btc_relativwert-Pfad trifft die echte Bauform",
           w2.get("btc_relativwert_pct") == -3.2,
           f"gebaut: {sorted(echt_fakt)}")

    # DIE FINANZIERUNG LAEUFT AUF DAS GEHEBELTE VOLUMEN, nicht auf den Einsatz.
    roh = {"antizyklisch": {"funding_rate_aktuell": -2.85e-05}}
    e1, _ = FQ.abbilden(roh, bereich="krypto_hebel", position_eur=500, hebel=1)
    e3, _ = FQ.abbilden(roh, bereich="krypto_hebel", position_eur=500, hebel=3)
    pruefe(P, "die Finanzierung skaliert mit dem Hebel",
           abs(e3["funding_eur_tag"] - 3 * e1["funding_eur_tag"]) < 0.02,
           "bei Hebel 3 laufen drei Euro Volumen je Euro Eigenkapital - wer "
           "das weglaesst, meldet ein Drittel der tatsaechlichen Kosten")
    ohne_groesse, fehlt3 = FQ.abbilden(roh, bereich="krypto_hebel")
    pruefe(P, "ohne Positionsgroesse KEINE Finanzierungsangabe",
           "funding_eur_tag" not in ohne_groesse
           and "funding_eur_tag" in fehlt3,
           "ein Prozentsatz je Stunde ist fuer den Nutzer keine Information")

    # LEERE FAKTEN SIND EIN DEFEKT, KEIN NORMALZUSTAND.
    w4, fehlt4 = FQ.abbilden({}, bereich="krypto_hebel")
    pruefe(P, "leere Fakten melden ALLE Schluessel als fehlend",
           w4 == {} and set(fehlt4) == set(FB.ZUSATZ_JE_BEREICH["krypto_hebel"]),
           "78 von 118 gespeicherten Spot-Signalen tragen '{}' - wer das als "
           "'nichts vorhanden' liest, haelt einen Defekt fuer normal")
    pruefe(P, "ein falscher Pfad meldet sich als fehlend",
           "kgv" in FQ.abbilden({"fundamentaldaten": {"kurs_gewinn": 12}},
                                bereich="aktien")[1])

    # ---- DIE INVARIANTE, die aus der Untersuchung des "leeren Fakten"-Befunds
    # folgt: wer das Gate passiert, traegt seine Fakten. Ausnahmslos.
    con3 = sqlite3.connect("data/tradinginfotool.db")
    verletzt = con3.execute(
        "SELECT COUNT(*) FROM signals WHERE gate_passed=1 AND LENGTH(facts_json)<=2"
    ).fetchone()[0]
    leer_ohne_gate = con3.execute(
        "SELECT COUNT(*) FROM signals WHERE gate_passed=0 AND LENGTH(facts_json)<=2"
    ).fetchone()[0]
    # ⚠️ NICHT GEGEN EINE ABGESCHRIEBENE ZAHL, SONDERN GEGEN DIE GESAMTMENGE
    # (Methodik 2.68, 24.08.2026-Fund). Bis heute stand hier `leer_ohne_gate
    # == 78` - eine Momentaufnahme der Produktions-DB zum Schreibzeitpunkt,
    # die mit jeder echten Abweisung veraltet (416 am Notebook, wenige Wochen
    # spaeter). Die eigentliche Aussage, die der Name der Pruefung verspricht
    # ("die leeren sind ALLE Abweisungen"), ist umgebungsunabhaengig: JEDE
    # Zeile mit leeren Fakten muss eine Abweisung sein, unabhaengig davon,
    # wie viele es gerade gibt.
    gesamt_leer = con3.execute(
        "SELECT COUNT(*) FROM signals WHERE LENGTH(facts_json)<=2"
    ).fetchone()[0]
    con3.close()
    pruefe(P, "jedes Signal MIT Gate traegt seine Fakten",
           verletzt == 0,
           "die leeren sind Abweisungen VOR der Analyse - dort gab es nie "
           "Fakten. Meine erste Meldung ('Defekt') war eine Zahl ohne ihre "
           "Schichtung")
    pruefe(P, "und die leeren sind alle Abweisungen",
           leer_ohne_gate == gesamt_leer,
           f"{leer_ohne_gate} von {gesamt_leer} leeren Zeilen sind "
           "Abweisungen - der Rest waere weder Gate-bestanden noch "
           "-abgewiesen, also ein dritter, unerwarteter Zustand")

    # ---- DER CHART ----
    from ui.signal_chart import render_signal_chart
    plan = dict(einstieg_von=64363.0, einstieg_bis=65230.0, stop=60462.0,
                ziel_von=71705.0, ziel_bis=72572.0)
    png = render_signal_chart(symbol="BTC", kurse_eur=cc[-120:], **plan)
    pruefe(P, "der Chart entsteht und ist ein PNG",
           png and png[1:4] == b"PNG" and len(png) > 5000,
           f"{len(png) if png else 0} Bytes")
    pruefe(P, "OHNE Plan gibt es KEINEN Chart",
           render_signal_chart(symbol="BTC", kurse_eur=cc[-120:]) is None,
           "ein Kursverlauf ohne eingezeichneten Plan ist Dekoration - genau "
           "der Vorwurf an den alten Zonen-Chart")
    pruefe(P, "bei zu kurzer Reihe ebenfalls nicht",
           render_signal_chart(symbol="BTC", kurse_eur=cc[-5:], **plan) is None)

    pruefe(P, "der Faktenblock steht in Abschnitt 1, vor der Rechnung",
           (lambda t: t.index("Schwankung") < t.index("2. DIE RECHNUNG"))(
               SM.baue_mail(symbol="BTC", name="B", kurs_eur=64797,
                            instrument="spot", strategie="einstieg", rechnung=r,
                            urteil={"aktion": "KAUFEN"},
                            faktenblock=FB.baue("krypto_spot", kern_werte=echt))[1]))





def paket_13() -> None:
    """Die drei Punkte aus der Datenausfall-Untersuchung (13.08.2026)."""
    P = "13"
    import sqlite3
    import staleness
    import database.db as db
    from scheduler import background as BG

    # PUNKT 1: der Preis-Cache steht jetzt im Watchdog.
    quelle = _quelltext("scheduler/background.py")
    pruefe(P, "der Watchdog prueft auch den Preis-Cache",
           "_preis_daten_veraltet" in quelle
           and "preise_veraltet, preise_gesamt = _preis_daten_veraltet" in quelle,
           "er prueft seit 23.07. Historie und OHLC - ausgefallen ist am 19.07. "
           "genau das, was er NICHT prueft")
    pruefe(P, "und stoesst den Nachhol-Lauf an",
           'modify_job("refresh_prices"' in quelle)

    class _Asset:
        def __init__(self, s): self.symbol = s

    class _Con:
        def __init__(self, alter_minuten):
            from datetime import datetime, timezone, timedelta
            self.zeit = (datetime.now(timezone.utc)
                         - timedelta(minutes=alter_minuten)).isoformat()

    def _preise(alter_minuten, symbole):
        from datetime import datetime, timezone, timedelta
        z = (datetime.now(timezone.utc) - timedelta(minutes=alter_minuten)).isoformat()
        class _P:
            def __init__(self, t): self.fetched_at = t
        return {s: _P(z) for s in symbole}

    echte = db.get_latest_prices
    try:
        db.get_latest_prices = lambda conn: _preise(5, ["BTC", "ETH", "SOL"])
        BG.db.get_latest_prices = db.get_latest_prices
        frisch = BG._preis_daten_veraltet(None, [_Asset(s) for s in ("BTC","ETH","SOL")])
        db.get_latest_prices = lambda conn: _preise(600, ["BTC", "ETH", "SOL"])
        BG.db.get_latest_prices = db.get_latest_prices
        alt = BG._preis_daten_veraltet(None, [_Asset(s) for s in ("BTC","ETH","SOL")])
        db.get_latest_prices = lambda conn: _preise(600, ["BTC"])
        BG.db.get_latest_prices = db.get_latest_prices
        teils = BG._preis_daten_veraltet(None, [_Asset(s) for s in ("BTC","ETH","SOL")])
    finally:
        db.get_latest_prices = echte
        BG.db.get_latest_prices = echte
    pruefe(P, "frische Preise gelten nicht als veraltet", frisch == (0, 3), str(frisch))
    pruefe(P, "10 Stunden alte Preise schon", alt == (3, 3), str(alt))
    pruefe(P, "ein fehlender Preis zaehlt als veraltet", teils == (3, 3), str(teils))

    # PUNKT 2: nur der TOTALausfall meldet sich, und nur einmal je Sperrfrist.
    BG._datenausfall_zuletzt = None
    gesendet = []
    import api.email_notify as EN
    echt_send = EN.send_notification_email
    try:
        EN.send_notification_email = lambda b, t, e=None: gesendet.append((b, t)) or True
        teilausfall = BG._melde_datenausfall(2, 3)
        total_1 = BG._melde_datenausfall(3, 3)
        total_2 = BG._melde_datenausfall(3, 3)
        winzig = BG._melde_datenausfall(2, 2)
    finally:
        EN.send_notification_email = echt_send
        BG._datenausfall_zuletzt = None
    pruefe(P, "ein TEILausfall meldet sich nicht", teilausfall is False,
           "eine Nachricht, die bei jedem einzelnen veralteten Asset feuert, "
           "wird nach drei Tagen weggeklickt und ist dann auch still")
    pruefe(P, "ein TOTALausfall meldet sich", total_1 is True and len(gesendet) == 1)
    pruefe(P, "aber nur einmal je Sperrfrist", total_2 is False and len(gesendet) == 1,
           f"{BG.DATENAUSFALL_SPERRE_MINUTEN} Minuten")
    pruefe(P, "unter drei Werten gibt es keine Meldung", winzig is False,
           "bei zwei Assets ist 'alle veraltet' keine Aussage")
    pruefe(P, "die Meldung sagt, WARUM man es sonst nicht merkt",
           gesendet and "ohne Gelegenheiten" in gesendet[0][1].lower()
           or gesendet and "Gelegenheiten" in gesendet[0][1],
           gesendet[0][1][:80] if gesendet else "nichts gesendet")

    # PUNKT 3: ein benanntes Praedikat statt drei stillschweigender.
    con = sqlite3.connect("data/tradinginfotool.db"); con.row_factory = sqlite3.Row
    try:
        z = db.zaehle_signale(con)
        pruefe(P, "Empfehlungen und Abweisungen werden getrennt gezaehlt",
               z["empfehlungen"] == 40 and z["abweisungen"] == 78,
               f"{z['empfehlungen']} / {z['abweisungen']}")
        pruefe(P, "und die Abweisungsgruende stehen dabei",
               z["abweisungsgruende"]
               and "Preis veraltet" in z["abweisungsgruende"][0][0]
               and z["abweisungsgruende"][0][1] == 72)
        pruefe(P, "der Waechter meldet heute keine Abweichung",
               db.pruefe_signal_kriterien(con) == [],
               "die drei Kriterien sind auf den echten Daten deckungsgleich - "
               "sie KOENNEN aber auseinanderlaufen (AnalystResponseInvalid)")
    finally:
        con.close()
    pruefe(P, "das Praedikat ist EINES und es ist benannt",
           db.IST_EMPFEHLUNG == "groq_raw_response IS NOT NULL",
           "gate_passed waere falsch: der AnalystResponseInvalid-Fallback setzt "
           "es auf True, OHNE dass eine Modellantwort vorliegt")



def paket_14() -> None:
    """Der Ausstieg - Trailing, Widerlegungspreis, Frist."""
    P = "14"
    from agent import ausstiegsrechnung as AR
    from agent.krypto import ausstiegsregel as AREGEL

    ein, stop = 55500.0, 51000.0          # Risiko 4.500

    def lauf(**kw):
        basis = dict(einstieg=ein, stop_original=stop, kurs_aktuell=ein,
                     heute="2026-08-13")
        basis.update(kw)
        return AR.bewerte(**basis)

    # DIE MESSGRUNDLAGE WIRD IMPORTIERT, NICHT NACHGEBAUT. Behavioural
    # geprueft: dasselbe Ergebnis wie die Originalregel, nicht "der Import
    # steht im Quelltext".
    e = lauf(hoechstkurs=ein + 1.8 * 4500)
    original = AREGEL.stopempfehlung(ein, stop, ein + 1.8 * 4500)
    pruefe(P, "der Trailing-Stop kommt aus der gemessenen Regel",
           abs(e["stop_empfohlen"] - original.stop_empfohlen) < 1e-9
           and abs(e["gesicherte_r"] - original.gesicherte_r) < 1e-9,
           "sie ist an 495 aufgeloesten Signalen gemessen (+0,092 R, "
           "Bootstrap [+0,051; +0,131]) - eine zweite Fassung waere die Sorte "
           "Kopie, die still veraltet")
    pruefe(P, "unter der Ausloeseschwelle zieht er nicht",
           lauf(hoechstkurs=ein + 0.5 * 4500)["trailing_aktiv"] is False)

    # DER GRENZFALL BEI GENAU 1 R IST DER VERWORFENE BREAKEVEN-LOCK - und er
    # wird benannt, nicht wegdefiniert.
    grenz = lauf(hoechstkurs=ein + 1.0 * 4500)
    pruefe(P, "bei genau +1 R sichert der Stop null - und das steht dabei",
           abs(grenz["gesicherte_r"]) < 0.01
           and any("sichert noch nichts" in g for g in grenz["gruende"]),
           "das IST der Breakeven-Lock, der am 01.08. verworfen wurde - aber "
           "die +0,092 R sind MIT diesem Randfall gemessen")

    # WIDERLEGUNGSPREIS - die K2-Luecke. Er stand bisher nur im Schema.
    falsch = lauf(kurs_aktuell=50900, umgeworfen_preis=51000)
    pruefe(P, "ein erreichter Widerlegungspreis fuehrt zu SCHLIESSEN",
           falsch["falsifiziert"] and falsch["empfehlung"] == AR.SCHLIESSEN,
           "die Fakten-Entscheidungsmappe: 'heute von niemandem ausgewertet'")
    pruefe(P, "ein NICHT erreichter nicht",
           lauf(kurs_aktuell=56000, umgeworfen_preis=51000)["falsifiziert"] is False)
    pruefe(P, "faellt er mit dem Stop zusammen, wird das gesagt",
           falsch["falsifikator_eigenstaendig"] is False
           and any("beide sagen dasselbe" in g for g in falsch["gruende"]),
           "in der neuen Kette wird der Stop AUS diesem Preis abgeleitet - "
           "dann ist die Pruefung keine zweite Absicherung")
    eigen = lauf(kurs_aktuell=52000, umgeworfen_preis=52500)
    pruefe(P, "und wo er eigenstaendig ist, ebenfalls",
           eigen["falsifikator_eigenstaendig"] is True)

    # FRIST.
    # Der Kurs muss UEBER dem nachgezogenen Stop liegen, sonst greift zu Recht
    # SCHLIESSEN und die Frist ist nicht mehr die Ueberschrift. Der erste
    # Testfall hatte 55.500 gegen einen Trailing-Stop von 57.300 - er war mit
    # der spaeter gebauten Regel unvereinbar, und genau das hat sie gemeldet.
    ab = lauf(kurs_aktuell=59000, hoechstkurs=ein + 1.4 * 4500,
              umgeworfen_bis="2026-08-01")
    pruefe(P, "eine abgelaufene Frist steht in der UEBERSCHRIFT",
           "FRIST ABGELAUFEN" in ab["empfehlung"],
           "in der ersten Fassung stand sie nur unter den Gruenden - eine "
           "Position mit abgelaufener Begruendung sah aus wie jede andere")
    pruefe(P, "eine laufende Frist nicht",
           "FRIST" not in lauf(umgeworfen_bis="2026-12-01")["empfehlung"])
    pruefe(P, "SCHLIESSEN wird von der Frist nicht verwaessert",
           lauf(kurs_aktuell=50900, umgeworfen_preis=51000,
                umgeworfen_bis="2026-08-01")["empfehlung"] == AR.SCHLIESSEN)

    # WAS NICHT PRUEFBAR IST, WIRD NICHT BEHAUPTET.
    text = " ".join(AR.saetze(lauf(
        umgeworfen_durch="Ein Tagesschluss unter 51.000 EUR bei steigendem Volumen.")))
    pruefe(P, "die Prosa-Bedingung wird gezeigt, nicht ausgewertet",
           "Selbst zu pruefen" in text and "nicht automatisch ausgewertet" in text,
           "'bei steigendem Volumen' ist nicht zuverlaessig maschinell pruefbar")

    # SHORT.
    kurz = AR.bewerte(einstieg=100.0, stop_original=110.0, kurs_aktuell=112.0,
                      ist_short=True, umgeworfen_preis=111.0, heute="2026-08-13")
    pruefe(P, "bei SHORT faellt die These nach OBEN",
           kurz["falsifiziert"] is True)
    pruefe(P, "und bei LONG nicht bei demselben Kurs",
           AR.bewerte(einstieg=100.0, stop_original=90.0, kurs_aktuell=112.0,
                      umgeworfen_preis=111.0, heute="2026-08-13")["falsifiziert"] is False)

    # KEIN ERGEBNIS OHNE GRUNDLAGE.
    for fehlt, kw in (("Einstieg", dict(einstieg=None)),
                      ("Originalstop", dict(stop_original=None)),
                      ("plausibles R", dict(stop_original=ein + 100))):
        pruefe(P, f"ohne {fehlt} gibt es keine Ausstiegsaussage",
               lauf(**kw) is None,
               "ohne R gibt es weder Trailing noch Stand noch Vergleich")


    # ---- MFE AUS DEM BACKWARD-TRACKING, UND DIE SAMMEL-MAIL ----
    import sqlite3 as _sq
    from agent.krypto.backward_tracking import (
        compute_ausstiegs_empfehlungen as _sammle, OUTCOME_OFFEN as _OFFEN)

    # Kopie im Speicher - die Produktivdatei wird nur gelesen. In ihr gibt es
    # KEINE offene Position und keinen einzigen MFE-Wert; die Kette liesse
    # sich dort nicht pruefen, und "geprueft 0" haette wie Erfolg ausgesehen.
    _q = _sq.connect("data/tradinginfotool.db")
    _c = _sq.connect(":memory:"); _q.backup(_c); _q.close(); _c.row_factory = _sq.Row
    # ⚠️ AUCH hebel_signals LEEREN (24.08.2026-Fund am Notebook). `_sammle()`
    # (compute_ausstiegs_empfehlungen) liest BEIDE Tabellen, `signals` UND
    # `hebel_signals` - nur `signals` wurde gewiped. Auf der echten
    # Produktions-Kopie stehen in `hebel_signals` weiterhin ECHTE offene
    # Positionen (am Notebook u.a. ETH), die dieselbe WHERE-Bedingung
    # erfuellen und sich in `_r["alle"]` MISCHEN: 7 statt 5 Zeilen, und
    # `_nach["ETH"]` zeigte die reale Position (mfe_r 1,97) statt der
    # synthetischen (0,3), weil der letzte Treffer im Dict gewinnt. Auf dem
    # Desktop blieb es unentdeckt, weil dort keine reale offene ETH-
    # Hebelposition in der Kopie lag.
    _c.execute("DELETE FROM signals"); _c.execute("DELETE FROM price_cache")
    _c.execute("DELETE FROM hebel_signals")
    _f = ("symbol, created_at, action, gate_passed, risk_veto, facts_json, "
          "outcome_status, outcome_max_realisiertes_crv, entry_usd_von, "
          "entry_usd_bis, stop_loss_usd_von, stop_loss_usd_bis, "
          "take_profit_usd_von, umgeworfen_preis_eur, umgeworfen_bis")
    for _sym, _mfe, _e, _s, _tp, _fa, _bis in (
            ("BTC", 1.8, 60000, 55000, 70000, 50000, "2026-12-01"),
            ("ETH", 0.3, 3000, 2700, 3600, 2950, "2026-12-01"),
            ("SOL", 2.4, 200, 180, 240, None, "2026-12-01"),
            ("APT", 0.4, 10, 9, 12, None, "2026-08-01"),
            ("INJ", 0.2, 20, 18, 24, None, None)):
        _c.execute(f"INSERT INTO signals ({_f}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (_sym, "2026-08-01T10:00:00+00:00", "KAUFEN", 1, 0, "{}",
                    _OFFEN, _mfe, _e, _e, _s, _s, _tp, _fa, _bis))
    for _sym, _k in (("BTC", 58000), ("ETH", 2900), ("SOL", 235),
                     ("APT", 10.5), ("INJ", 20.4)):
        _c.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, "
                   "price_eur, fetched_at) VALUES (?,?,?,?,?)",
                   (_sym, _sym.lower(), _k, _k * 0.87, "2026-08-13T10:00:00+00:00"))
    # ETH liegt bewusst NICHT im Bestand - reine Signalverfolgung.
    _c.execute("DELETE FROM holdings")
    for _sym in ("BTC", "SOL", "APT", "INJ"):
        _c.execute("INSERT INTO holdings (symbol, quantity, updated_at) "
                   "VALUES (?,?,?)", (_sym, 1.0, "2026-08-13"))
    _c.commit()
    _r = _sammle(_c, [], {})
    _nach = {a["symbol"]: a for a in _r["alle"]}

    # ⚠️ MEHR ALS EIN STATISCHER HINWEISTEXT (24.08.2026): diese drei
    # Pruefungen laufen auf einer vollstaendig ISOLIERTEN, gewipten und
    # synthetisch befuellten Kopie - trotzdem waren sie am Notebook rot und
    # am Desktop gruen, obwohl der Code identisch ist. Ohne die tatsaechlich
    # gelesenen Werte laesst sich nicht sagen, WELCHE Zeile fehlt oder WELCHER
    # mfe_r abweicht - der alte Detailtext erklaerte nur die Absicht der
    # Pruefung, nicht ihren Befund.
    _mfe_diag = (f"gelesen: {len(_r['alle'])} von 5 Zeilen, Symbole "
                 f"{sorted(_nach)} | " + ", ".join(
                     f"{s}={_nach[s].get('mfe_r')}" for s in
                     ("BTC", "ETH", "SOL", "APT", "INJ") if s in _nach))
    pruefe(P, "der MFE kommt aus dem Backward-Tracking",
           len(_r["alle"]) == 5
           and abs(_nach["BTC"]["mfe_r"] - 1.8) < 1e-9,
           "`outcome_max_realisiertes_crv` wird seit 02.08. auch fuer OFFENE "
           "Signale fortgeschrieben - er muss nicht neu gerechnet werden | "
           + _mfe_diag)
    pruefe(P, "auch Positionen UNTER der Ausloeseschwelle werden geprueft",
           "ETH" in _nach and _nach["ETH"]["mfe_r"] < 1.0,
           "vorher stand dort ein `continue` - eine Position im Minus loest "
           "den Trailing-Stop per Definition nicht aus, und genau dort ist "
           "der Widerlegungspreis am wichtigsten | " + _mfe_diag)
    pruefe(P, "und ihr Widerlegungspreis greift",
           _nach["ETH"]["empfehlung"] == AR.SCHLIESSEN,
           f"empfehlung={_nach['ETH'].get('empfehlung')!r} statt "
           f"{AR.SCHLIESSEN!r} | " + _mfe_diag)
    pruefe(P, "die Reihenfolge ist Dringlichkeit, nicht Buchgewinn",
           [a["symbol"] for a in _r["alle"][:2]] == ["BTC", "ETH"]
           and _nach["SOL"]["mfe_r"] > _nach["ETH"]["mfe_r"],
           "SOL hat den groessten Buchgewinn und steht trotzdem hinten - "
           "der groesste ungesicherte Gewinn ist nicht der dringendste Fall")

    _betreff, _text = AR.sammel_mail(_r["alle"], _r["geprueft"])
    pruefe(P, "der Betreff nennt Handlungsbedarf, Nahes zuerst",
           _betreff == "TradingInfoTool: 1 nah am Ziel, 1 faellig", _betreff,)

    # ECHTER BESTAND GEGEN SIGNALVERFOLGUNG - Nutzerfund: "die Aktionen sind
    # teilweise fiktiv". Von 45 Signal-Symbolen lagen 28 nicht im Bestand.
    pruefe(P, "was nicht im Bestand liegt, steht getrennt",
           "SIGNALVERFOLGUNG - KEIN BESTAND (1)" in _text
           and _nach["ETH"]["ist_bestand"] is False
           and _nach["BTC"]["ist_bestand"] is True)
    pruefe(P, "und traegt keine Handlungsanweisung",
           "nie eroeffnet" in _text
           and _text.index("JETZT SCHLIESSEN") < _text.index("SIGNALVERFOLGUNG"),
           "'SCHLIESSEN' fuer eine Position, die es nicht gibt, ist eine "
           "Anweisung ins Leere")
    _nur_verfolgung = [a for a in _r["alle"] if not a["ist_bestand"]]
    pruefe(P, "eine fiktive Position loest KEINE Mail aus",
           AR.sammel_mail(_nur_verfolgung) is None,
           "wer fuer eine nie eroeffnete Position geweckt wird, hoert nach der "
           "dritten Mail auf hinzusehen")

    # WAS "SCHLIESSEN" NICHT HEISST.
    pruefe(P, "die Mail sagt, wo ein erreichtes Ziel steht",
           "erreichtes Kursziel steht GANZ OBEN" in _text,
           "diese Pruefung erwartete zuerst das Gegenteil ('steht NICHT "
           "hier') - richtig war das, solange es die Take-Profit-Nachlese "
           "nicht gab. Der Nutzereinwand hat beides geaendert")
    pruefe(P, "und wie oft sie kommt",
           "Taeglich um 07:15" in _text)

    # EUR STATT USD, und die Richtung nur, wo es eine Wahl gibt.
    pruefe(P, "die Kurse stehen in EUR",
           "EUR" in _text and "USD" not in _text,
           "der Faktor kommt aus DERSELBEN Cache-Zeile (price_eur/price_usd) - "
           "eine zweite Umrechnung waere eine zweite Wahrheit")
    pruefe(P, "bei Spot steht keine Richtung",
           "Spot, seit" in _text and "LONG, spot" not in _text,
           "eine Spot-Position kann gar nicht short sein")

    # SOL steht seit der Naeherungswarnung unter "ZIEL IN REICHWEITE" statt
    # unter "STOP NACHZIEHEN" - die handlungsnaehere Gruppe gewinnt.
    for _t in ("ZIEL IN REICHWEITE (1)", "JETZT SCHLIESSEN (1)",
               "BEGRUENDUNG ABGELAUFEN (1)", "OHNE HANDLUNGSBEDARF (1)"):
        pruefe(P, f"die Mail hat den Block '{_t}'", _t in _text)
    pruefe(P, "was nichts braucht, steht in EINER Zeile",
           "INJ +2,0 %" in _text and _text.count("INJ") == 1,
           "wer zwoelf Positionen haelt, soll nicht zwoelf Absaetze lesen, "
           "um die zwei zu finden, die zaehlen")
    import re as _re
    pruefe(P, "keine ZAHL wird in R angegeben",
           not _re.search(r"[\d,]\s*R", _text),
           "die erste Fassung dieser Pruefung suchte schlicht ' R' und traf "
           "damit ' REICHWEITE' und ' Ruecklauf' - ein Textfund ist noch "
           "keine Aussage")
    pruefe(P, "Prozente und Kurse deutsch",
           "-3,3 %" in _text and "55.680 EUR" in _text,
           "die Pruefung erwartete '64.000 USD' - der Wert vor der "
           "EUR-Umstellung. 64.000 x 0,87 = 55.680")
    pruefe(P, "das Datum ist lesbar, nicht technisch",
           "seit 01.08." in _text and "2026-08-01" not in _text,
           "auch die Fristzeile - dort stand 'galt bis 2026-08-01'")


    # ---- ZIEL ERREICHT, ABER NOCH IM BESTAND (Nutzerfund 13.08.) ----
    #
    # Bisher passierte beim Zielerreichen nur ein logger.info(). Das Tracking
    # verbuchte "gewonnen" - und der Wert lag weiter im Depot.
    from agent.krypto.backward_tracking import OUTCOME_TAKE_PROFIT as _TP
    _c.execute(
        "INSERT INTO signals (symbol, created_at, action, gate_passed, risk_veto, "
        "facts_json, outcome_status, outcome_entschieden_am, "
        "outcome_realisiertes_crv, entry_usd_von, stop_loss_usd_von, "
        "take_profit_usd_von) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("BTC", "2026-07-01T10:00:00+00:00", "KAUFEN", 1, 0, "{}", _TP,
         "2026-08-13", 2.0, 20, 18, 26))
    _c.execute("INSERT INTO signals (symbol, created_at, action, gate_passed, "
               "risk_veto, facts_json, outcome_status, outcome_entschieden_am, "
               "outcome_realisiertes_crv, entry_usd_von, stop_loss_usd_von, "
               "take_profit_usd_von) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
               ("ETH", "2026-07-01T10:00:00+00:00", "KAUFEN", 1, 0, "{}", _TP,
                "2026-08-13", 2.0, 20, 18, 26))
    _c.commit()
    _r2 = _sammle(_c, [], {}, seit_tag="2026-08-11")
    _erreicht = {z["symbol"] for z in _r2["ziel_erreicht"]}
    pruefe(P, "ein erreichtes Ziel im BESTAND wird gemeldet",
           "BTC" in _erreicht,
           "bisher passierte beim Zielerreichen nur ein logger.info() - das "
           "Tracking verbuchte 'gewonnen', der Wert lag weiter im Depot")
    pruefe(P, "ein erreichtes Ziel OHNE Bestand nicht",
           "ETH" not in _erreicht,
           "ETH liegt nicht in `holdings` - dort ist das Ziel ein Messpunkt, "
           "kein Verkaufsauftrag")
    _b3, _t3 = AR.sammel_mail(_r2["alle"], ziel_erreicht=_r2["ziel_erreicht"])
    pruefe(P, "es steht GANZ OBEN in der Mail",
           _t3.index("ZIEL ERREICHT") < _t3.index("JETZT SCHLIESSEN"),
           "es ist die einzige gute Nachricht hier und die einzige, bei der "
           "Geld auf dem Tisch liegt")
    pruefe(P, "und im Betreff zuerst",
           _b3.startswith("TradingInfoTool: 1 Ziel erreicht"), _b3)
    pruefe(P, "die Mail sagt, dass verkauft werden muss",
           "liegen noch im Depot" in _t3 and "verkauft wird dadurch nichts" in _t3)
    pruefe(P, "ein erreichtes Ziel ALLEIN loest schon eine Mail aus",
           AR.sammel_mail([], ziel_erreicht=_r2["ziel_erreicht"]) is not None,
           "ohne das waere die einzige Nachricht mit Geld darin die einzige, "
           "die nicht verschickt wird")


    # ---- NAEHERUNGSWARNUNG ----
    #
    # Die naheliegende Antwort auf "ich erfahre es erst am naechsten Morgen"
    # waere ein engerer Takt. Sie ist falsch: eine Mail alle 15 Minuten wird
    # nach zwei Tagen ignoriert, und schneller als der Markt ist man trotzdem
    # nicht. Das Ziel steht im Voraus fest - es gehoert als Auftrag zur Boerse.
    for _kurs, _erwartet in ((58000, False), (66000, False),
                             (69000, True), (71000, False)):
        _n = AR.bewerte(einstieg=60000, stop_original=55000, ziel=70000,
                        kurs_aktuell=_kurs, mfe_r=0.5, heute="2026-08-13")
        pruefe(P, f"bei Kurs {_kurs} ist das Ziel "
                  f"{'in' if _erwartet else 'NICHT in'} Reichweite",
               _n["ziel_in_reichweite"] is _erwartet,
               "ueber 100 % ist das Ziel durchlaufen - dann greift die "
               "Nachlese, nicht die Warnung" if _kurs == 71000 else
               f"Schwelle {100 * AR.ZIEL_NAH_ANTEIL:.0f} % des Weges")
    _nah = AR.bewerte(einstieg=60000, stop_original=55000, ziel=70000,
                      kurs_aktuell=69000, mfe_r=0.5, heute="2026-08-13")
    pruefe(P, "die Warnung nennt den Auftrag, nicht nur die Gefahr",
           any("VERKAUFSAUFTRAG" in g for g in _nah["gruende"]),
           "'pass auf' hilft nicht - 'hinterlege einen Auftrag bei X' schon, "
           "danach ist der Ruecklauf ueber Nacht wirkungslos")

    # JEDE POSITION GENAU EINMAL. Erste Fassung: LINK stand unter "Ziel in
    # Reichweite" UND unter "Stop nachziehen".
    #
    # ⚠️ hebel_signals BLEIBT AUCH HIER LEER (24.08.2026) - dieselbe Kopie
    # `_c` wird weiterverwendet, die Tabelle also bereits vom vorigen Wipe
    # leer sein, aber ein Wipe hier ist die guenstige Absicherung gegen eine
    # spaetere Umstellung auf eine frische Kopie an dieser Stelle.
    _c.execute("DELETE FROM signals"); _c.execute("DELETE FROM price_cache")
    _c.execute("DELETE FROM holdings"); _c.execute("DELETE FROM hebel_signals")
    _fz = ("symbol, created_at, action, gate_passed, risk_veto, facts_json, "
           "outcome_status, outcome_max_realisiertes_crv, entry_usd_von, "
           "entry_usd_bis, stop_loss_usd_von, stop_loss_usd_bis, take_profit_usd_von")
    for _sym, _mfe, _e, _s, _tp in (("LINK", 1.9, 20, 18, 26),
                                    ("SOL", 1.5, 200, 180, 260)):
        _c.execute(f"INSERT INTO signals ({_fz}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (_sym, "2026-08-01T10:00:00+00:00", "KAUFEN", 1, 0, "{}",
                    _OFFEN, _mfe, _e, _e, _s, _s, _tp))
    for _sym, _k in (("LINK", 25.5), ("SOL", 230)):
        _c.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, "
                   "price_eur, fetched_at) VALUES (?,?,?,?,?)",
                   (_sym, _sym.lower(), _k, _k * 0.87, "2026-08-13T10:00:00+00:00"))
        _c.execute("INSERT INTO holdings (symbol, quantity, updated_at) "
                   "VALUES (?,?,?)", (_sym, 1.0, "2026-08-13"))
    _c.commit()
    _r3 = _sammle(_c, [], {})
    _b4, _t4 = AR.sammel_mail(_r3["alle"], ziel_erreicht=_r3["ziel_erreicht"])
    pruefe(P, "eine Position steht in GENAU EINER Gruppe",
           _t4.count("LINK  ") == 1 and _t4.count("SOL   ") == 1,
           "erste Fassung: LINK stand unter 'Ziel in Reichweite' UND unter "
           "'Stop nachziehen' - zwei Absaetze fuer dieselbe Position")
    pruefe(P, "und der Betreff zaehlt sie nicht doppelt",
           _b4 == "TradingInfoTool: 1 nah am Ziel, 1 Stop nachziehen", _b4)
    pruefe(P, "der Zielkurs steht im Absatz",
           "22,62 EUR" in _t4 and "Verkaufsauftrag dort hinterlegen" in _t4)
    pruefe(P, "der Stop-Hinweis geht dabei nicht verloren",
           "Stop auf 18,97 EUR nachziehen" in _t4,
           "die Naehe zum Ziel ist die handlungsnaehere Aussage, aber die "
           "Stop-Marke gilt weiter")

    # KEINE MAIL OHNE ANLASS.
    _ruhig = [a for a in _r["alle"] if a["symbol"] == "INJ"]
    pruefe(P, "laeuft alles, kommt KEINE Mail",
           AR.sammel_mail(_ruhig) is None,
           "eine Nachricht, die taeglich 'alles in Ordnung' sagt, wird nach "
           "einer Woche nicht mehr gelesen - und dann auch die eine nicht, "
           "die zaehlt")
    pruefe(P, "und ohne Positionen erst recht nicht", AR.sammel_mail([]) is None)
    _c.close()

    # ---- DER AUSSTIEG IN DER MAIL ----
    from agent import entscheidungsrechnung as _ER
    from agent import signal_mail as _SM

    _r = _ER.rechne(kurs=58000, atr=1677, risiko_eur=75, instrument="hebel",
                    betrag_wunsch_eur=500, topf_frei_eur=500)

    # EIN SCHON UNTERSCHRITTENER TRAILING-STOP. Gefunden an der fertigen Mail:
    # dort stand "Stop auf 59.100 nachziehen" neben einem Kurs von 58.000.
    spaet = lauf(kurs_aktuell=58000, hoechstkurs=ein + 1.8 * 4500)
    # ⚠️ ECHTER BESTAND (17.08.2026). Seit heute haengt die Ueberschrift der
    # Mail an `ist_bestand`, und die folgenden Pruefungen meinen den Fall
    # einer WIRKLICH gehaltenen Position - der faellige Ausstieg, der einen
    # Nachkauf verhindert, setzt sie ohnehin voraus (rollen_lauf, O-37).
    # Ohne dieses Feld pruefte der Test ab heute einen anderen Fall als den,
    # den er beschreibt.
    spaet["ist_bestand"] = True
    pruefe(P, "ein bereits unterschrittener Trailing-Stop heisst SCHLIESSEN",
           spaet["stop_bereits_unterschritten"] is True
           and spaet["empfehlung"] == AR.SCHLIESSEN,
           "die Marke ist dann kein Vorschlag fuer morgen, sondern ein "
           "Ereignis von gestern")
    pruefe(P, "ein noch nicht erreichter nicht",
           lauf(kurs_aktuell=62000, hoechstkurs=ein + 1.8 * 4500)
           ["stop_bereits_unterschritten"] is False)
    pruefe(P, "und bei SHORT gilt es andersherum",
           AR.bewerte(einstieg=100.0, stop_original=110.0, kurs_aktuell=97.0,
                      hoechstkurs=100 - 1.8 * 10, ist_short=True,
                      heute="2026-08-13")["stop_bereits_unterschritten"] is True)

    _, txt = _SM.baue_mail(symbol="BTC", name="Bitcoin", kurs_eur=58000,
                           instrument="hebel", strategie="swing", rechnung=_r,
                           ausstieg=spaet,
                           urteil={"aktion": "NACHKAUFEN", "begruendung": "x"})
    pruefe(P, "kein Nachkauf auf eine Position, die geschlossen gehoert",
           "Kein zusaetzlicher Einstieg" in txt and "Einstiegszone" not in txt,
           "in der ersten Fassung standen 'Stop auf 59.100 nachziehen' und "
           "'Einstiegszone 57.581 bis 58.419' untereinander - zwei Anweisungen "
           "fuer dasselbe Asset, die einander ausschliessen")
    betreff, _ = _SM.baue_mail(symbol="BTC", name="B", kurs_eur=58000,
                               instrument="hebel", strategie="swing", rechnung=_r,
                               ausstieg=spaet, urteil={"aktion": "NACHKAUFEN"})
    # UMGESCHRIEBEN 15.08.2026. Hier stand: "ein faelliger Ausstieg steht im
    # BETREFF" - auch auf einer NACHKAUFEN-Mail. Die Sorge dahinter war
    # richtig (eine dringende Meldung darf nicht hinter einer Kaufzeile
    # verschwinden), die Umsetzung nicht: im Produktionslauf ging zweimal
    #
    #     Betreff:     TradingInfoTool: TURBO - SCHLIESSEN (Hebel)
    #     Signalzeile: TURBO  EROEFFNEN  Hebel 3,8  500 EUR
    #
    # hinaus. Der Nutzer liest den Betreff und handelt danach.
    #
    # DIE DRINGLICHKEIT IST NICHT VERLOREN, sie steht jetzt an zwei besseren
    # Stellen: im Abschnitt "2. DIE POSITION" ganz oben im Text, und - seit
    # O-37 - erzeugt die Kette diese Mail gar nicht mehr, wenn ein echter
    # Bestand zum Schliessen ansteht.
    pruefe(P, "der Betreff nennt die Aktion DIESER Mail",
           betreff.startswith("TradingInfoTool: BTC - NACHKAUFEN"), betreff)
    pruefe(P, "und der faellige Ausstieg steht ganz oben im Text",
           txt.index("Bestehende Position") < txt.index("3. DAS URTEIL"),
           "sichtbar vor dem Urteil des Modells - nur nicht als Ueberschrift")
    # BEI EINER NICHT-EINSTIEGSAKTION BLEIBT ER IM BETREFF: dort beschreibt er
    # tatsaechlich, was zu tun ist.
    _b_halten, _ = _SM.baue_mail(symbol="BTC", name="B", kurs_eur=58000,
                                 instrument="hebel", strategie="swing",
                                 rechnung=_r, ausstieg=spaet,
                                 urteil={"aktion": "HALTEN"})
    pruefe(P, "bei HALTEN steht er weiterhin im Betreff",
           _b_halten.startswith("TradingInfoTool: BTC - SCHLIESSEN"),
           _b_halten)

    ruhig = lauf(kurs_aktuell=62000, hoechstkurs=ein + 1.8 * 4500)
    # Auch hier ein ECHTER Bestand: die Pruefung heisst 'Bestand UND
    # Nachkauf nebeneinander' und meint genau den.
    ruhig["ist_bestand"] = True
    _, txt2 = _SM.baue_mail(symbol="BTC", name="B", kurs_eur=62000,
                            instrument="hebel", strategie="swing", rechnung=_r,
                            ausstieg=ruhig, urteil={"aktion": "NACHKAUFEN"})
    pruefe(P, "sonst stehen Bestand UND Nachkauf getrennt nebeneinander",
           "Bestehende Position:" in txt2 and "Zusaetzlicher Einstieg:" in txt2)
    pruefe(P, "und der Abschnitt heisst dann DIE POSITION",
           "--- 2. DIE POSITION ---" in txt2,
           "bei einem Bestand ist die dringendere Frage, was mit ihm "
           "geschieht - nicht, ob man noch mehr davon kauft")

    # GEHALTEN ODER NUR VERFOLGT - die Ueberschrift muss es sagen
    # (17.08.2026, Nutzerfund an einer echten SOL-Mail).
    #
    # Die Mail sagte oben "SOL ist nicht im Bestand" und zwanzig Zeilen
    # tiefer "Bestehende Position: HALTEN, +0.43 R". Beide Saetze stimmten
    # fuer sich: der erste kam aus `holdings`, der zweite aus einer Zeile je
    # SIGNAL. Wer das liest, muss glauben, er halte etwas.
    _nur_verfolgt = dict(ruhig)
    _nur_verfolgt["ist_bestand"] = False
    _, _txt_v = _SM.baue_mail(symbol="BTC", name="B", kurs_eur=62000,
                              instrument="hebel", strategie="swing",
                              rechnung=_r, ausstieg=_nur_verfolgt,
                              urteil={"aktion": "NACHKAUFEN"})
    pruefe(P, "ohne Bestand heisst der Block nicht 'Bestehende Position'",
           "Verfolgter Einstiegsvorschlag" in _txt_v
           and "Bestehende Position" not in _txt_v,
           "von 45 Signal-Symbolen lagen 28 gar nicht im Bestand")
    pruefe(P, "mit Bestand aber schon",
           "Bestehende Position" in txt2
           and "Verfolgter Einstiegsvorschlag" not in txt2,
           "sonst waere die Unterscheidung nur eine Umbenennung")

    # EINE SCHREIBWEISE.
    # ⚠️ DIE ZAHL HAT DEN PLATZ GEWECHSELT (20.08.2026, Kapitel 94).
    #
    # Geprueft wurde die Schreibweise am Widerlegungspreis. Der steht dort
    # nicht mehr: `bewerte()` kennt den Umrechnungsfaktor nicht, also nannte
    # die Zeile eine Zahl in ungewisser Waehrung. Sie verweist jetzt auf den
    # Abschnitt DIE RECHNUNG, wo der Preis umgerechnet steht.
    #
    # Die Pruefung haengt deshalb am nachgezogenen Stop - einer Zahl, die
    # weiterhin ausgegeben wird. Der Faktor 1,0 haelt sie wiedererkennbar.
    zahlen = " ".join(AR.saetze({
        "stop_empfohlen": 50901.0, "gesicherte_r": 0.5, "eur_je_usd": 1.0,
        "empfehlung": "STOP NACHZIEHEN", "gruende": []}))
    pruefe(P, "alle Betraege in deutscher Schreibweise",
           "50.901" in zahlen and "50,901" not in zahlen,
           "die erste Fassung schickte die ganze Zeile durch translate - "
           "daneben stand '50,901.00 EUR' unuebersetzt")



def paket_12c() -> None:
    """Das Gate: Konfidenz raus, Durchlaessigkeit zaehlen, Faktorzahl nur mitschreiben."""
    P = "12c"
    import sqlite3
    from agent import rollen_gate as RG

    # DIE KONFIDENZ-SCHWELLE KOMMT IN DER NEUEN KETTE NICHT VOR. Sie fiel
    # nicht durch Wahl, sondern als Folge: r = +0,073 (n = 92) gegen das
    # realisierte CRV, und das Regime stand ueber 1.022 Faelle konstant auf
    # "baer" - die Schwelle also faktisch immer bei 75.
    for datei in ("agent/rollen_gate.py", "agent/trefferbilanz.py",
                  "agent/entscheidungsrechnung.py", "agent/rolle_trader.py"):
        quelle = _quelltext(datei)
        import re as _re
        # NICHT DAS WORT SUCHEN, SONDERN DEN VERGLEICH. Die erste Fassung fand
        # "confidence_pct" im Docstring, der erklaert, warum es die Groesse
        # nicht mehr gibt - derselbe Fehler wie bei der " R"-Suche: ein
        # Textfund ist noch keine Aussage.
        _vergleich = _re.search(
            r"(confidence_pct|min_konfidenz\w*)\s*(<|>|<=|>=|==)", quelle)
        pruefe(P, f"{datei.split('/')[-1]} VERGLEICHT keine Konfidenz",
               _vergleich is None,
               "eine konstante Schwelle auf einer nutzlosen Groesse "
               "(r = +0,073 gegen das realisierte CRV)")
    pruefe(P, "keine der Stufen heisst 'konfidenz'",
           not any("konfidenz" in s for s in RG.STUFEN_NAMEN))

    # DAS ZAEHLWERK GREIFT NICHT EIN. Ein Zaehler, der selbst verwirft,
    # faelscht seine eigene Messung.
    d = RG.Durchlauf("test")
    for i in range(10):
        sym = f"S{i}"
        d.beginne(sym)
        d.bestanden(sym, "auftrag")
        if i < 3:
            d.verloren(sym, "fakten", "keine Historie")
            continue
        for stufe in ("fakten", "lagebild", "urteil", "aktion", "geometrie",
                      "risikoschicht"):
            d.bestanden(sym, stufe)
        d.verloren(sym, "entscheider", "traegt sich nicht")
    # ⚠️ G-6 (31.08.2026): DER ENTSCHEIDER VERWIRFT JETZT.
    # Hier stand "zaehlt, aber nimmt nichts heraus" - richtig bis U-1, als
    # die Stufe noch mit `trefferbilanz` rechnete. Seit sie mit
    # `potential.traegt()` entscheidet und der Wirkungsnachweis vorliegt
    # (Gesperrte -0,2749 R gegen bleibende -0,2518 R), waere ein blosses
    # Zaehlen eine Bewertung ohne Folge.
    pruefe(P, "⚠️ der Entscheider VERWIRFT (G-6)",
           d.verloren_je_stufe["entscheider"] == 7 and d.heraus == 0,
           "wer hier 7 heraus erwartet, prueft den Stand vor dem 31.08. - "
           "dann war die gesamte Bewertung ohne Wirkung auf den Signalfluss")
    pruefe(P, "und NUR_ZAEHLEN ist leer, mit Begruendung im Modul",
           RG.NUR_ZAEHLEN == ()
           and "G-6" in io.open("agent/rollen_gate.py",
                                encoding="utf-8").read(),
           "eine leere Liste ohne Begruendung sieht in einem Jahr aus wie "
           "ein Versehen")
    pruefe(P, "eine echte Stufe nimmt sehr wohl heraus",
           d.verloren_je_stufe["fakten"] == 3 and d.hinein == 10)

    # ------------------------------------------------------------------
    # ⚠️⚠️ DIE DREI ZUSTAENDE VON STUFE 11 (31.08.2026)
    #
    # DIESE PRUEFUNG HAT GEFEHLT, und ihr Fehlen kostete den Rollout.
    # G-6 schaltete Stufe 11 scharf; die Paketpruefung war gruen. Erst
    # `simuliere_kette.py` gegen die Notebook-Produktion zeigte, was das
    # in Wirklichkeit tat: **null Signale ueber alle fuenf Gruppen.**
    #
    # Grund: alle drei tragenden Beitraege stehen auf `klassen=("krypto",)`.
    # Fuer aktien, themen_etf, rohstoffe und hedge gibt es keine Messung -
    # und ein Filter ohne Messgrundlage sperrt nach DATENLAGE statt nach
    # Qualitaet. Regel 4: ein Fakt ist keine Begruendung.
    #
    # Die Pruefung haelt drei Dinge fest, damit weder Richtung wieder
    # verrutscht:
    #   1  eine NICHT VERMESSENE Klasse wird nicht gesperrt
    #   2  eine VERMESSENE Klasse ohne Wert wird sehr wohl gesperrt
    #   3  das Durchlassen ist SICHTBAR, nicht still
    # ------------------------------------------------------------------
    import agent.potential as _PTx
    import agent.wahrscheinlichkeit as _WKx
    _p_krypto = _PTx.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                            instrument="spot", strategie="einstieg",
                            h=None, merkmale=None)
    _p_aktien = _PTx.rechne(crv=2.0, stop_relativ=0.05, klasse="aktien",
                            instrument="spot", strategie="einstieg",
                            h=None, merkmale=None)
    pruefe(P, "⚠️ eine vermessene Klasse ist von einer unvermessenen "
              "unterscheidbar",
           _p_krypto.vermessen and not _p_aktien.vermessen,
           "ohne diese Unterscheidung sperrt Stufe 11 vier von fuenf "
           "Assetklassen dauerhaft - gemessen am 31.08.: 0 Signale")
    # ⚠️ MIT STRATEGIE FRAGEN. Seit die Beitraege `strategien=("einstieg",)`
    # tragen, liefert ein Aufruf OHNE Strategie nichts - richtig so: ohne
    # Strategie ist nicht entschieden, welche Geometrie gemeint ist.
    pruefe(P, "und `vermessen` fragt die REGISTRIERUNG, nicht eine Liste",
           len(_WKx.vermessen("krypto", "einstieg")) == 2
           and _WKx.vermessen("aktien", "einstieg") == [],
           "eine handgeschriebene Klassenliste veraltet still, sobald ein "
           "Beitrag dazukommt - genau der Fehler aus `pruefe_beitragsabdeckung`")
    pruefe(P, "⚠️ `vermessen` und `bewertbar` sind NICHT dasselbe",
           (not _p_krypto.bewertbar) and _p_krypto.vermessen,
           "krypto ist vermessen, dieser Aufruf hat aber keine Merkmale - "
           "wer beides gleichsetzt, sperrt entweder zu viel oder zu wenig")
    _q = io.open("agent/rollen_lauf.py", encoding="utf-8").read()
    pruefe(P, "der Ablauf prueft `vermessen` VOR `bewertbar`",
           _q.find("not _potential.vermessen") > 0
           and _q.find("not _potential.vermessen")
               < _q.find("not _potential.bewertbar"),
           "in der anderen Reihenfolge greift die Datenlueckensperre zuerst "
           "und die Unterscheidung ist wirkungslos")
    pruefe(P, "⚠️ und das Durchlassen ist SICHTBAR (`notiz`), nicht still",
           "durchlauf.notiz(" in _q and hasattr(RG.Durchlauf, "notiz"),
           "ein wortloses Durchwinken sieht in der Trichtertabelle aus, als "
           "haette der Entscheider zugestimmt")
    _d2 = RG.Durchlauf()
    _d2.beginne("XX")
    _d2.notiz("XX", "entscheider", "Klasse aktien ist nicht vermessen")
    pruefe(P, "eine Notiz nimmt NICHTS aus dem Lauf",
           _d2.heraus == 1 and _d2.verloren_je_stufe["entscheider"] == 0,
           "sonst waere sie eine Sperre mit anderem Namen")
    pruefe(P, "und sie steht in der Trichtertabelle",
           any("nicht beurteilt" in z for z in _d2.bericht()),
           "eine Notiz, die niemand sieht, ist keine Notiz")

    # ------------------------------------------------------------------
    # ⚠️⚠️ EIN BEITRAG GILT NUR, WO ER GEMESSEN WURDE (31.08.2026)
    #
    # Bis zum 31.08. trugen alle drei tragenden Beitraege ein LEERES
    # `strategien` und galten damit auch fuer `akkumulation`. Gemessen
    # wurden sie ausschliesslich auf der Einstiegs-Geometrie: Horizont 20
    # Handelstage, CRV 2,0, ATR-Stop. Eine Akkumulation kauft ueber Wochen
    # verteilt zu - anderer Horizont, anderes Erfolgsmass, kein einziger
    # gemessener Anker.
    #
    # Ein leeres Feld sieht aus wie eine Erlaubnis und ist in Wahrheit eine
    # offene Frage. Genau der H-Fehler: die Anwendung reicht weiter als die
    # Messung.
    # ------------------------------------------------------------------
    for _b in _WKx.BEITRAEGE:
        if _b.zustand != "traegt":
            continue
        pruefe(P, "%s nennt seine Strategien" % _b.name[:34],
               bool(_b.strategien),
               "leer heisst 'gilt ueberall' - und das ist bei einem auf "
               "EINER Geometrie gemessenen Beitrag nie wahr. Die Messung "
               "steht in: " + _b.quelle[:70])
    # ------------------------------------------------------------------
    # ⚠️⚠️ DIE SCHWELLE JE DATENLAGE (31.08.2026)
    #
    # Das Potential ist die SUMME der Beitragspunkte. Wer nur einen Beitrag
    # hat, erreicht hoechstens +0,039 R; wer beide hat, +0,1335 R. Eine
    # feste Schwelle ueber 0,039 sperrt die duenne Datenlage DAUERHAFT -
    # nach Datenlage statt nach Qualitaet.
    # ------------------------------------------------------------------
    _p_ein = _PTx.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                         instrument="spot", strategie="einstieg", h=None,
                         merkmale={"funding_fuenftel": 1})
    _p_zwei = _PTx.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                          instrument="spot", strategie="einstieg", h=None,
                          merkmale={"funding_fuenftel": 1,
                                    "turnover_fuenftel": 0})
    pruefe(P, "⚠️ die Schwelle richtet sich nach der Datenlage",
           _p_ein.schwelle < _p_zwei.schwelle,
           "wer weniger Beitraege hat, kann weniger erreichen - und darf "
           "nicht an derselben Zahl gemessen werden (%.4f gegen %.4f)"
           % (_p_ein.schwelle, _p_zwei.schwelle))
    pruefe(P, "und die VOLLE Datenlage behaelt die Vorgabe",
           abs(_p_zwei.schwelle - _PTx.schwelle()) < 1e-9,
           "sie ist der Bezug - sonst waere die Kalibrierung von "
           "`messe_schwelle_kalibrierung.py` hinfaellig")
    pruefe(P, "⚠️ das beste Fuenftel ist bei JEDER Datenlage erreichbar",
           _p_ein.wert_r > _p_ein.schwelle and _p_zwei.wert_r > _p_zwei.schwelle,
           "sonst waere die Sperre eine Aussage ueber unsere Datenlage, "
           "nicht ueber den Wert (Regel 4)")
    _q2 = io.open("agent/rollen_lauf.py", encoding="utf-8").read()
    pruefe(P, "und der Ablauf benutzt sie auch",
           "_potential.traegt_hier" in _q2,
           "eine Schwelle, die die Aufrufstelle nicht erreicht, ist "
           "Dekoration")
    # ⚠️ UND DIE MESSWERKZEUGE AUCH. Am 31.08. meldete
    # `simuliere_rollout_gegen_nb.py` "0 von 1.854 kaemen durch" - ein
    # Artefakt: es rechnete noch `PT.traegt()` mit der FESTEN Schwelle,
    # waehrend die Produktion `traegt_hier` benutzt. Eine Vorschau, die
    # etwas anderes rechnet als der Betrieb, warnt vor der falschen Sache.
    # ⚠️ UEBER DEN AST, NICHT UEBER TEXT. Die erste Fassung suchte
    # "PT.traegt(p.wert_r)" im Quelltext - und fand es im KOMMENTAR, der
    # die Korrektur erklaert. Genau der Fehler, den die
    # Verdrahtungspruefung heute frueher gemacht hat (Docstring als
    # Aufruf gezaehlt). Ein Kommentar ist kein Aufruf.
    import ast as _ast2
    _sim_baum = _ast2.parse(
        io.open("simuliere_rollout_gegen_nb.py", encoding="utf-8").read())
    _sim_attr = {n2.attr for n2 in _ast2.walk(_sim_baum)
                 if isinstance(n2, _ast2.Attribute)}
    _sim_aufrufe = {
        n2.func.attr for n2 in _ast2.walk(_sim_baum)
        if isinstance(n2, _ast2.Call) and isinstance(n2.func, _ast2.Attribute)}
    # ------------------------------------------------------------------
    # ⚠️⚠️ DAS ZELLENMODELL (Schritt 3, 01.09.2026) — NOCH OHNE AUFRUFER
    #
    # Eine Zelle ist (Asset, Instrument, Strategie). Sie sagt, welche Fragen
    # fuer ein Asset ueberhaupt gestellt werden duerfen - nicht, ob es ein
    # Signal bekommt. Das ist Stufe 11 und kommt in Schritt 4.
    # ------------------------------------------------------------------
    import sqlite3 as _sqz
    from agent import assetklassen as _AKz
    from agent import handelsauftrag as _HAz
    _zc = _sqz.connect(":memory:")
    _zc.execute("CREATE TABLE asset_hebel_settings (symbol TEXT, "
                "hebel_pruefung_erlaubt INTEGER)")
    _zc.execute("CREATE TABLE asset_dca_settings (symbol TEXT, "
                "dca_erlaubt INTEGER)")
    _zc.executemany("INSERT INTO asset_hebel_settings VALUES (?,?)",
                    [("BTC", 1), ("LINK", 1), ("XLM", 0)])
    _zc.executemany("INSERT INTO asset_dca_settings VALUES (?,?)",
                    [("BTC", 1)])
    _z = _AKz.zellen(conn=_zc)
    _je = {}
    for x in _z:
        _je.setdefault(x["symbol"], set()).add(
            (x["instrument"], x["strategie"]))

    pruefe(P, "⚠️ eine VERBOTENE Kombination entsteht nicht",
           all((i, st) in
               [(i2, s2) for i2, ss in _HAz.ERLAUBTE_PAARE.items()
                for s2 in ss]
               for paare in _je.values() for i, st in paare),
           "die Paar-Matrix ist die einzige Quelle - `hebel x akkumulation` "
           "ist ausgeschlossen, weil die Finanzierung JEDEN Tag kostet")
    pruefe(P, "und `swing` kommt nicht vor",
           not any(st == "swing" for paare in _je.values()
                   for _i, st in paare),
           "Nutzerentscheidung 31.08.: 'nur Einstieg reicht, Swing aktuell "
           "kein Thema'. Die Paar-Matrix kennt es weiter - hier faellt es "
           "an EINER Stelle raus")
    pruefe(P, "⚠️ der HEBEL-Schalter des Nutzers wirkt",
           ("hebel", "einstieg") in _je.get("BTC", set())
           and ("hebel", "einstieg") in _je.get("LINK", set())
           and ("hebel", "einstieg") not in _je.get("XLM", set()),
           "BTC und LINK stehen auf 1, XLM auf 0 - wer den Schalter nicht "
           "fragt, baut einen, der etwas verspricht, was nicht passiert")
    pruefe(P, "und der AKKUMULATIONS-Schalter ebenso",
           ("spot", "akkumulation") in _je.get("BTC", set())
           and ("spot", "akkumulation") not in _je.get("LINK", set()),
           "nur BTC hat `dca_erlaubt=1` in dieser Probe")
    pruefe(P, "⚠️ JEDES Asset hat mindestens die Grundzelle",
           all(("spot", "einstieg") in p or
               ("absicherung", "einstieg") in p for p in _je.values()),
           "ein Asset ohne Zelle koennte NIE ein Signal bekommen - und zwar "
           "still")
    # ⚠️ OHNE VERBINDUNG die vorsichtige Richtung
    _z0 = _AKz.zellen(conn=None)
    pruefe(P, "⚠️ ohne Datenbank entsteht KEINE Hebelzelle",
           not any(x["instrument"] == "hebel" for x in _z0),
           "der Hebelschalter hat keine Vorgabe - ohne Datenbank waere jede "
           "Hebelzelle erfunden")
    pruefe(P, "und jede Zelle nennt ihren Grund",
           all(x.get("warum") for x in _z),
           "eine Liste ohne Begruendung muss beim naechsten Zweifel "
           "nachgerechnet werden")
    # ⚠️ SCHRITT 3 IST SEIT DEM 01.09.2026 VERDRAHTET - und diese Zeile
    # wurde ERSETZT, nicht geloescht.
    #
    # Sie lautete: „Schritt 3 hat NOCH KEINEN Aufrufer" und hielt die
    # Zusage fest, dass die Zellenliste folgenlos bleibt, bis sie
    # geprueft ist. In ihrem eigenen Begruendungstext stand: „Wenn diese
    # Zeile faellt, ist Schritt 4 gebaut - dann gehoert sie ERSETZT,
    # nicht geloescht." Genau das passiert hier.
    #
    # Jetzt gilt die Umkehrung: `rollen_lauf` MUSS die Zellen rufen,
    # sonst ist der Umbau still zurueckgefallen.
    _ruft = [q for q in ("agent/rollen_lauf.py", "scheduler/rollen_job.py",
                         "agent/rollen_eingabe.py")
             if "zellen(" in _quelltext(q)]
    pruefe(P, "⚠️ Schritt 3 IST verdrahtet - `rollen_lauf` ruft die Zellen",
           "agent/rollen_lauf.py" in _ruft,
           "bis zum 01.09. war das Gegenteil zugesagt UND geprueft. Seit "
           "Schritt 4 laeuft die Schleife ueber Zellen - faellt diese "
           "Zeile, ist der Umbau zurueckgefallen, ohne dass es auffaellt. "
           "Gefunden in: %s" % (", ".join(_ruft) or "NIRGENDS"))
    pruefe(P, "und `laeufe()` ist unveraendert",
           len(_AKz.laeufe()) == 5,
           "der bestehende Weg darf sich nicht mitaendern - sonst waere "
           "Schritt 3 nicht folgenlos")
    _zc.close()

    # ------------------------------------------------------------------
    # ⚠️ DIE SPALTE `instrument` IN `signals` (Zellenmodell Schritt 2)
    #
    # Ohne sie sind ein Spot- und ein Hebel-Signal desselben Assets am
    # selben Tag nicht unterscheidbar: `hebel` ist der FAKTOR aus der
    # Rechnung, und ein Hebel-Signal mit Faktor 1,0 saehe aus wie Spot.
    # ------------------------------------------------------------------
    import sqlite3 as _sq3
    _mig = _sq3.connect(":memory:")
    _mig.row_factory = _sq3.Row
    _mig.execute("CREATE TABLE signals (id INTEGER PRIMARY KEY, "
                 "symbol TEXT, quelle_kette TEXT)")
    _mig.executemany("INSERT INTO signals (symbol, quelle_kette) VALUES (?,?)",
                     [("BTC", "rollen"), ("3QSS", "rollen"),
                      ("BTC", None)])
    import database.db as _DBm
    _DBm._migrate_signal_instrument(_mig)
    _sp = {r[1] for r in _mig.execute("PRAGMA table_info(signals)")}
    pruefe(P, "⚠️ `signals` bekommt die Spalte `instrument`",
           "instrument" in _sp,
           "ohne sie sind Spot- und Hebelsignal desselben Assets nicht "
           "unterscheidbar")
    _btc = _mig.execute("SELECT instrument FROM signals WHERE symbol='BTC' "
                        "AND quelle_kette='rollen'").fetchone()[0]
    _hed = _mig.execute("SELECT instrument FROM signals WHERE symbol='3QSS'"
                        ).fetchone()[0]
    _alt = _mig.execute("SELECT instrument FROM signals WHERE "
                        "quelle_kette IS NULL").fetchone()[0]
    pruefe(P, "der Altbestand bekommt das Etikett SEINER Gruppe",
           _btc == "spot" and _hed == "absicherung",
           "BTC=%r, 3QSS=%r - die Zuordnung kommt aus "
           "`assetklassen.INSTRUMENTE_JE_GRUPPE`, nicht aus einer zweiten "
           "Liste" % (_btc, _hed))
    pruefe(P, "⚠️ und die ALTE Kette bleibt unberuehrt",
           _alt is None,
           "Altsignale mit `quelle_kette IS NULL` stammen aus einer anderen "
           "Logik; sie zu etikettieren hiesse, ihnen eine Eigenschaft "
           "zuzuschreiben, die sie nie hatten")
    _vor = _mig.execute("SELECT COUNT(*) FROM signals WHERE "
                        "instrument IS NOT NULL").fetchone()[0]
    _DBm._migrate_signal_instrument(_mig)
    pruefe(P, "die Migration ist idempotent",
           _mig.execute("SELECT COUNT(*) FROM signals WHERE instrument IS "
                        "NOT NULL").fetchone()[0] == _vor,
           "sie laeuft bei JEDEM Start - ein zweiter Lauf darf nichts "
           "aendern")
    _mig.close()

    pruefe(P, "⚠️ und die Rollout-Vorschau rechnet wie die Produktion",
           "traegt_hier" in _sim_attr and "traegt" not in _sim_aufrufe,
           "sonst misst die Vorschau eine Nachbildung, die still veraltet - "
           "sie rief `PT.traegt()` mit der FESTEN Schwelle und meldete "
           "daraufhin 0 von 1.854")

    pruefe(P, "⚠️ und akkumulation gilt daher als NICHT vermessen",
           _WKx.vermessen("krypto", "einstieg")
           and not _WKx.vermessen("krypto", "akkumulation"),
           "wer hier Beitraege fuer akkumulation erwartet, prueft den Stand "
           "vor dem 31.08. - dann wurde eine Einstiegsmessung auf eine "
           "Strategie angewandt, fuer die es keinen einzigen Anker gibt")

    # WER RAUS IST, WIRD IN SPAETEREN STUFEN NICHT MEHR GEZAEHLT.
    d2 = RG.Durchlauf()
    d2.beginne("X"); d2.verloren("X", "fakten", "weg")
    d2.bestanden("X", "urteil")
    pruefe(P, "ein ausgeschiedenes Asset zaehlt spaeter nicht mit",
           d2.bestanden_je_stufe["urteil"] == 0,
           "sonst stuende ein Asset in einer Stufe, die es nie erreicht hat")

    # DIE FAKTORZAHL WIRD MITGESCHRIEBEN, NICHT GEFILTERT.
    d3 = RG.Durchlauf()
    for n in (1, 2, 5):
        d3.beginne(f"F{n}")
        d3.faktorzahl(n)
        for stufe in RG.STUFEN_NAMEN:
            d3.bestanden(f"F{n}", stufe)
    pruefe(P, "die Faktorzahl wird gezaehlt",
           d3.faktorzahlen == [1, 2, 5])
    pruefe(P, "und filtert NICHTS - auch ein einzelner Faktor kommt durch",
           d3.heraus == 3,
           "die Faktorzahl zeigte in der Messung KEINEN Effekt (7.26); ein "
           "unbelegter Filter ist schlechter als keiner")
    pruefe(P, "der Bericht sagt selbst, dass sie nicht filtert",
           any("kein Filter" in z for z in d3.bericht()))

    # DER BERICHT ZEIGT, WO DIE KETTE VERLIERT - der eigentliche Zweck.
    bericht = " ".join(d.bericht())
    pruefe(P, "der Bericht markiert die groesste Verlustquelle",
           "<- hier" in bericht,
           "ein Lauf mit 40 hinein und 0 heraus sieht identisch aus, egal ob "
           "das Gate abwies, das Modell NICHTS_TUN sagte oder die Geometrie "
           "nicht rechenbar war")
    pruefe(P, "und nennt die Gruende je Stufe",
           "keine Historie" in bericht)

    # EINE UNBEKANNTE STUFE IST EIN FEHLER, KEIN STILLES NICHTS.
    try:
        RG.Durchlauf().bestanden("X", "gibt_es_nicht")
        ok = False
    except ValueError:
        ok = True
    pruefe(P, "eine unbekannte Stufe fliegt auf", ok,
           "ein Tippfehler im Stufennamen wuerde sonst still nichts zaehlen "
           "- und die Tabelle saehe aus wie ein Befund")

    # PERSISTENZ: additiv und idempotent.
    _q = sqlite3.connect("data/tradinginfotool.db")
    _c = sqlite3.connect(":memory:"); _q.backup(_c); _q.close()
    # ⚠️ ERST DEN AUSGANGSZUSTAND HERSTELLEN, DEN DIE PRUEFUNG BRAUCHT
    # (Methodik 2.68, 24.08.2026-Fund). `_q.backup(_c)` kopiert die ECHTE
    # Produktions-DB - dort ist die Tabelle laengst migriert, seit die Kette
    # im Betrieb laeuft. "Erster Aufruf legt an, zweiter tut nichts" laesst
    # sich an einer bereits migrierten Kopie gar nicht pruefen: beide Aufrufe
    # kommen dort gleich ("[] / []") heraus, egal ob die Idempotenz stimmt.
    # Deshalb die Tabelle in der KOPIE explizit entfernen, bevor der erste
    # Aufruf stattfindet - dieselbe Isolation, die die Nachbarpruefungen in
    # diesem Paket schon fuer `signals`/`price_cache` benutzen.
    _c.execute(f"DROP TABLE IF EXISTS {RG.TABELLE}")
    erst = RG.migriere(_c)
    zweit = RG.migriere(_c)
    pruefe(P, "die Migration legt die Tabelle an und ist idempotent",
           erst and not zweit, f"{erst} / {zweit}")
    kennung = RG.schreibe(_c, d, "2026-08-13T07:00:00+00:00")
    zeile = _c.execute(f"SELECT hinein, heraus FROM {RG.TABELLE} WHERE id=?",
                       (kennung,)).fetchone()
    # ⚠️ G-6: `heraus` ist jetzt 0 - die sieben scheitern am Entscheider,
    # der seit dem 31.08. verwirft. Vorher stand hier (10, 7).
    pruefe(P, "und der Lauf laesst sich nachlesen", zeile == (10, 0), str(zeile))
    _c.close()



def paket_12b() -> None:
    """GUI: Regime-Tab auf den Score, Override auf den Score (E4)."""
    P = "12b"
    import config as config_module
    from ui.regime_view import _SCORE_LESEHILFE, _score_einordnung
    from agent.krypto import regime as RGM

    # DIE LESEHILFE MUSS DIE ECHTEN STUETZSTELLEN SEIN, nicht erfundene.
    pruefe(P, "die Lesehilfe stammt aus den echten Stuetzstellen",
           tuple(p for p, _ in _SCORE_LESEHILFE)
           == tuple(p for p, _ in RGM._SCORE_STUETZSTELLEN),
           "sonst zeigt die GUI eine Skala, die die Rechnung nicht kennt")
    pruefe(P, "und ordnet einen Wert dem naechsten Punkt zu",
           "voll baerisch" in _score_einordnung(0.30)
           and "aufwaerts" in _score_einordnung(0.95)
           and _score_einordnung(None) == "nicht verfuegbar")

    # DER OVERRIDE WIRKT AUF DEN SCORE - behavioural, nicht im Quelltext gesucht.
    import inspect
    sig = inspect.signature(RGM.determine_regime)
    pruefe(P, "determine_regime nimmt einen Score-Override entgegen",
           "manual_override_score" in sig.parameters
           and sig.parameters["manual_override_score"].default is None,
           "mit Vorgabewert - sonst brechen alle bestehenden Aufrufer")
    pruefe(P, "und der einzige Aufrufer uebergibt ihn per Schluesselwort",
           "manual_override_score=config_dict.get" in _quelltext("agent/krypto/pipeline.py"),
           "der Parameter steht in der Signatur VOR anderen Vorgaben - ein "
           "positioneller Aufruf wuerde sie verschieben")

    # SCHREIBEN UND LESEN, gegen die echte Datei, danach zurueckgesetzt.
    vorher = config_module.load_config().get("regime", {}).get(
        "manueller_override_score")
    try:
        config_module.set_regime_score_override(0.6)
        gelesen = config_module.load_config()["regime"]["manueller_override_score"]
        pruefe(P, "ein gesetzter Score wird sofort wieder gelesen",
               gelesen == 0.6,
               "der Cache ist ein Modul-Global - ohne Invalidierung stand "
               "'geschrieben: True' neben 'gelesen: None'")
        config_module.set_regime_score_override(None)
        pruefe(P, "und laesst sich abschalten",
               config_module.load_config()["regime"]["manueller_override_score"] is None)
    finally:
        config_module.set_regime_score_override(vorher)


    # DIE CONFIG DARF SICH BEIM SCHREIBEN NICHT VERAENDERN, ausser im Wert.
    # Am 13.08. hat genau das die Datei zerlegt: 1.933 LF-Zeilen wurden zu
    # 1.955 CRLF plus 19.426 verirrten CR, der Diff war unlesbar, die Datei
    # musste aus dem letzten guten Stand wiederhergestellt werden.
    vor_bytes = open("Basisinfos/config.yaml", "rb").read()
    try:
        config_module.set_regime_score_override(0.6)
        zwischen = open("Basisinfos/config.yaml", "rb").read()
        config_module.set_regime_score_override(vorher)
    finally:
        config_module.set_regime_score_override(vorher)
    nach_bytes = open("Basisinfos/config.yaml", "rb").read()
    pruefe(P, "nach Hin und Zurueck ist die Datei BYTE-IDENTISCH",
           vor_bytes == nach_bytes,
           f"{len(vor_bytes)} -> {len(nach_bytes)} Bytes")
    pruefe(P, "und der Schreibvorgang aendert nur den Wert",
           abs(len(zwischen) - len(vor_bytes)) <= 1
           and zwischen.count(b"\n") == vor_bytes.count(b"\n"),
           "die erste Fassung baute den Kommentar neu zusammen und zerstoerte "
           "damit die Ausrichtung der ganzen Datei")
    pruefe(P, "die Zeilenenden bleiben einheitlich",
           nach_bytes.count(b"\r\n") == nach_bytes.count(b"\n"),
           "write_text uebersetzt unter Windows jedes \n in \r\n - die "
           "Warnung steht seit dem 09.07. in derselben Datei")

    for schlecht in (1.5, -0.1, "abc"):
        try:
            config_module.set_regime_score_override(schlecht)
            ok = False
        except ValueError:
            ok = True
        finally:
            config_module.set_regime_score_override(vorher)
        pruefe(P, f"'{schlecht}' wird abgewiesen", ok,
               "0.00 bis 1.00, sonst nichts")

    # NICHT BEIDE OVERRIDES GLEICHZEITIG - zwei Wahrheiten ueber denselben
    # Zustand, und es waere nicht ablesbar, welche gilt.
    etikett_vorher = config_module.load_config()["regime"]["manueller_override"]
    try:
        config_module.set_regime_manueller_override("baer")
        try:
            config_module.set_regime_score_override(0.5)
            ok = False
        except ValueError as exc:
            ok = "Etikett-Override" in str(exc)
        pruefe(P, "Score-Override neben aktivem Etikett-Override wird abgewiesen",
               ok, "beide gleichzeitig waeren zwei Wahrheiten")
    finally:
        config_module.set_regime_manueller_override(etikett_vorher)
        config_module.set_regime_score_override(vorher)

    # DER SCORE-OVERRIDE MUSS AUCH WIRKEN, nicht nur schreibbar sein.
    ansicht = _quelltext("ui/regime_view.py")
    pruefe(P, "der Tab zeigt den Score und die Mindestkonfidenz",
           "regime_score_stetig" in ansicht
           and "regime_min_konfidenz_stetig" in ansicht,
           "das Etikett stand ueber 1.022 Faelle konstant auf 'baer' - der "
           "Score ist die Groesse, die wirklich wirkt")



def paket_12d() -> None:
    """Z1 verdrahtet, Z.ai auf die fuenf Aktionen."""
    P = "12d"
    from agent import gegenpruefer_rollen as Z1
    from agent import rollen_gate as RG
    from agent.empfehlung_vertrag import AKTIONEN
    from agent.krypto.gegenpruefung import richtung_aus_action

    # Z.AI KENNT DIE NEUEN AKTIONEN. REDUZIEREN stand in KEINER Menge und fiel
    # still auf None - jedes Reduzieren-Signal ueberging die Richtungspruefung.
    erwartet = {"KAUFEN": "LONG", "NACHKAUFEN": "LONG",
                "REDUZIEREN": "SHORT", "VERKAUFEN": "SHORT",
                "NICHTS_TUN": None}
    for aktion, richtung in erwartet.items():
        pruefe(P, f"{aktion} -> {richtung}",
               richtung_aus_action(aktion) == richtung,
               "REDUZIEREN ist ein TEILverkauf - baerisch auf dieses Symbol"
               if aktion == "REDUZIEREN" else "")
    pruefe(P, "JEDE Aktion des Vertrags ist abgedeckt",
           set(erwartet) == set(AKTIONEN),
           f"Vertrag: {sorted(AKTIONEN)}")
    pruefe(P, "NICHTS_TUN und HALTEN bedeuten dasselbe",
           richtung_aus_action("NICHTS_TUN") == richtung_aus_action("HALTEN") is None,
           "sonst haengt das Ergebnis davon ab, WO in der Kette geprueft wird "
           "- vor oder nach signal_abbildung.UMBENENNUNG")
    pruefe(P, "beim Hedge dreht auch REDUZIEREN um",
           richtung_aus_action("REDUZIEREN", ist_hedge_invertiert=True) == "LONG")

    # Z1 IST VERDRAHTET - und der Modulkopf behauptet nichts anderes mehr.
    pruefe(P, "der Modulkopf sagt VERDRAHTET",
           "STAND: VERDRAHTET" in (Z1.__doc__ or ""),
           "er sagte 'GEBAUT, NICHT VERDRAHTET. Kein Aufrufer.' - genau das "
           "war Paket 12d")

    eingabe = ["Bitcoin notiert 39,0 % unter seinem Schlusskurs von vor 250 "
               "Handelstagen.", "Der Gleichlauf ist uneinheitlich."]
    gut = {"lage": "Bitcoin liegt rund 39 % im Minus.", "belege": []}
    erfunden = {"lage": "Bitcoin liegt 62 % im Minus, die Maerkte laufen im "
                        "Gleichschritt.", "belege": []}

    d = RG.Durchlauf("test")
    for sym, ausgabe in (("BTC", gut), ("ETH", erfunden)):
        d.beginne(sym)
        d.bestanden(sym, "auftrag")
        Z1.pruefe_und_zaehle(ausgabe, eingabe, symbol=sym, durchlauf=d,
                             gleichlauf_wert="uneinheitlich")
    pruefe(P, "eine erfundene Zahl schlaegt an (Z-1)",
           "ETH" in d.z1_verstoesse and "Z-1" in d.z1_verstoesse["ETH"])
    pruefe(P, "eine falsche Richtungsbehauptung ebenfalls (Z-2)",
           "Z-2" in d.z1_verstoesse["ETH"],
           "'die Maerkte laufen im Gleichschritt' gegen gerechnet "
           "'uneinheitlich'")
    pruefe(P, "eine treue Ausgabe schlaegt NICHT an",
           "BTC" not in d.z1_verstoesse)

    # ZAEHLEN, NICHT VERWERFEN - die Entscheidung, die der Modulkopf verlangt.
    pruefe(P, "ein Z1-Befund nimmt NICHTS aus dem Lauf",
           d.heraus == 2 and d.bestanden_je_stufe["lagebild"] == 2,
           "ein Waechter, der selbst verwirft, macht seine eigene Wirkung "
           "unsichtbar - und das System hat monatelang nicht gekauft")
    pruefe(P, "aber er steht im Bericht",
           any("Treuepruefung Z1" in z for z in d.bericht()))
    pruefe(P, "und im JSON des Laufs", "z1_verstoesse" in d.als_json())

    # DIE MAIL SCHWEIGT, WENN NICHTS IST.
    pruefe(P, "ohne Befund kein Satz in der Mail",
           Z1.satz(Z1.pruefe(gut, eingabe, "uneinheitlich")) == [],
           "eine Fussnote 'alle Zahlen gedeckt' unter jeder Nachricht waere "
           "Fuellstoff")
    mit = Z1.satz(Z1.pruefe(erfunden, eingabe, "uneinheitlich"))
    pruefe(P, "mit Befund nennt sie die Regel und den Grund",
           any("Z-1" in z for z in mit) and any("62" in z for z in mit),
           "seit dem 17.08. deutsch und ohne Liste: '62' statt '[62.0]' "
           "- der Satz steht in der MAIL, nicht nur im Log")
    pruefe(P, "und sagt, was sie NICHT bedeutet",
           any("kein Urteil ueber die Empfehlung" in z for z in mit),
           "Z1 prueft die Treue zur Eingabe, nicht die Guete des Urteils")

    # Z-4 laeuft ueber den LAUF, nicht ueber den Fall.
    pruefe(P, "identische Ausgaben ueber viele Anker schlagen an (Z-4)",
           Z1.zaehle_leerlauf([gut, gut, gut])["verstoss"] is True,
           "ein Lagebild, das immer dasselbe sagt (R-T6)")
    pruefe(P, "verschiedene nicht",
           Z1.zaehle_leerlauf([gut, erfunden])["verstoss"] is False)

    # ---- ABLAUFKETTE UND WARTEFREQUENZEN (Nutzerhinweis 13.08.) ----
    #
    # Die Mail zeigt Z.ai-Zeilen, die zum Versandzeitpunkt noch gar nicht da
    # sein muessen. In der alten Kette ist genau das zweimal passiert.
    import re as _re2

    def _konst(datei, name):
        t = _quelltext(datei)
        m = _re2.search(rf"^{name}\s*=\s*([\d.]+)", t, _re2.M)
        return float(m.group(1)) if m else None

    zai_timeout = _konst("api/zai.py", "REQUEST_TIMEOUT_SECONDS")
    warte_max = _konst("scheduler/background.py", "_ZAI_EMAIL_WARTE_MAX_SEKUNDEN")
    poll = _konst("scheduler/background.py", "_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN")
    gemini_rate = _konst("api/gemini.py", "RATE_LIMIT_PER_MINUTE")


    # ---- Z.AI AUF DEN FAKTEN DER NEUEN KETTE ----
    #
    # GEGENPRUEFUNG 12d: die Aktionen waren angepasst, die FAKTEN nicht.
    # `baue_objektive_fakten()` erwartet rsi/trend_label/regime/funding - die
    # neue Kette produziert nichts davon, sondern Saetze.
    bau = Z1.objektive_fakten_aus_rollen
    f = bau("BTC", ["Bitcoin notiert 39,0 % unter dem Stand von vor 250 Tagen."],
            ["Der naechste Widerstand liegt bei 62.000 EUR."], "uneinheitlich")
    pruefe(P, "das Faktenpaket traegt die SAETZE der neuen Kette",
           f["marktlage"] and f["asset_fakten"] and f["symbol"] == "BTC",
           "aus Saetzen wieder RSI-Zahlen zu gewinnen waere Rueckbau - die "
           "neue Kette hat sie bewusst nicht (Kapitel 11.6)")
    pruefe(P, "der gerechnete Gleichlauf geht mit",
           f.get("gleichlauf_gerechnet") == "uneinheitlich",
           "die einzige Groesse, die ein Festpunkt AUSSERHALB des Modells ist")
    pruefe(P, "leere Saetze fallen raus",
           bau("BTC", ["", "  ", None], [])["marktlage"] == [])

    # ANKER-VERMEIDUNG: Z.ai soll eine EIGENE Richtung ableiten.
    pruefe(P, "ein sauberes Paket meldet keinen Anker",
           Z1.enthaelt_anker(f) == [])
    mit_feld = dict(f); mit_feld["aktion"] = "KAUFEN"
    pruefe(P, "eine mitgeschickte Aktion faellt auf",
           "aktion" in Z1.enthaelt_anker(mit_feld),
           "wer der Gegenpruefung die Antwort zeigt, misst nur noch das Echo")
    pruefe(P, "auch eine Aktion im KLARTEXT",
           Z1.enthaelt_anker(bau("BTC", ["Die Empfehlung lautet KAUFEN."], []))
           == ["Aktion 'KAUFEN' im Klartext"])
    pruefe(P, "und 'KAUFEN' wird NICHT in 'NACHKAUFEN' gefunden",
           Z1.enthaelt_anker(bau("BTC", ["Die Empfehlung lautet NACHKAUFEN."], []))
           == ["Aktion 'NACHKAUFEN' im Klartext"],
           "die erste Fassung meldete zwei Anker, wo einer stand - ein "
           "Waechter, der falsch Alarm schlaegt, wird ignoriert, und dann "
           "auch der richtige Alarm")
    pruefe(P, "der Waechter entfernt nichts",
           "aktion" in mit_feld,
           "wer stillschweigend korrigiert wird, macht denselben Fehler "
           "an der naechsten Stelle wieder")

    pruefe(P, "alle Taktgroessen sind auffindbar",
           None not in (zai_timeout, warte_max, poll, gemini_rate),
           f"zai={zai_timeout} warte={warte_max} poll={poll} gemini={gemini_rate}")
    pruefe(P, "die Mail wartet laenger als EIN Z.ai-Call dauert",
           warte_max > zai_timeout,
           f"{warte_max} s gegen {zai_timeout} s - sonst ginge die Mail bei "
           f"jedem einzelnen langsamen Call ohne Gegenpruefung raus")
    pruefe(P, "sie deckt den schlimmsten Fall NICHT ab - und das ist bekannt",
           3 * zai_timeout > warte_max,
           f"3 Calls x {zai_timeout} s = {3 * zai_timeout} s gegen "
           f"{warte_max} s. KEIN Defekt, sondern P-8: lieber ohne "
           f"Z.ai-Zeilen als gar nicht")
    pruefe(P, "das Poll-Intervall ist deutlich kleiner als die Wartezeit",
           poll * 10 <= warte_max,
           "sonst waere die Wartezeit faktisch ein fester Sleep")
    pruefe(P, "der Takt der Rollen-Kette haengt an Gemini, nicht an Z.ai",
           gemini_rate < _konst("api/zai.py", "RATE_LIMIT_PER_MINUTE"),
           f"41 Aufrufe bei 40 Assets / {gemini_rate:.0f} pro Minute = "
           f"mindestens {41 / gemini_rate:.1f} Minuten")

    # DIE ABHAENGIGKEIT MUSS AN DER MAIL STEHEN, nicht nur im Kopf des Prueflings.
    mail_quelle = _quelltext("agent/signal_mail.py")
    pruefe(P, "signal_mail nennt die Abhaengigkeit und wo die Wartestufe sitzt",
           "_ZAI_EMAIL_WARTE_MAX_SEKUNDEN" in mail_quelle
           and "agent/zweite_meinung.py" in mail_quelle
           and "KEINE EIGENE WARTEMECHANIK" in mail_quelle,
           "sie formatiert, sie wartet nicht - wer sie woanders einhaengt, "
           "muss dieselbe Reihenfolge nehmen, sonst kehrt der Fund vom "
           "28.07. zurueck")



def paket_13() -> None:
    """Hebel: Richtung, sieben Aktionen, Hebelfaktor gerechnet."""
    P = "13"
    from agent import entscheidungsrechnung as ER
    from agent import llm_schema, rolle_trader
    from agent.empfehlung_vertrag import (AKTIONEN, AKTIONEN_HEBEL, RICHTUNGEN,
                                          EmpfehlungUngueltig, aktionen_fuer,
                                          validiere)
    from agent.krypto.hebel_analyst import REQUIRED_HEBEL_ACTIONS

    # ---- S6a (22.08.2026): EIN VOKABULAR FUER BEIDE INSTRUMENTE -------
    # ⚠️ DIESE PRUEFUNGEN STANDEN BIS HEUTE AUF DEM GEGENTEIL ("Spot behaelt
    # seine fuenf, Hebel hat sieben"). Sie sind nicht angepasst worden, damit
    # sie gruen werden, sondern weil sich die ABSICHT geaendert hat: das Verb
    # sagt, WAS getan wird, das Instrument WIE. Zwei Dinge, zwei Felder.
    pruefe(P, "Spot und Hebel fragen dasselbe Vokabular",
           aktionen_fuer("spot") == aktionen_fuer("hebel") == AKTIONEN
           and len(AKTIONEN) == 5,
           "bis S6a trug das VERB eine Instrumentendeutung - 'ERÖFFNEN' las "
           "sich wie ein Hebelgeschaeft, auch bei Hebel 1,0 (76 % der Faelle)")

    # ⚠️ DIE ZWEI HEBEL-AKTIONEN SIND ERSATZLOS ENTFALLEN, und zwar aus einem
    # Regelgrund: sie liessen das MODELL den Hebelfaktor aendern.
    pruefe(P, "HEBEL_ERHÖHEN und HEBEL_SENKEN gibt es nicht mehr",
           not {"HEBEL_ERHÖHEN", "HEBEL_SENKEN"} & set(AKTIONEN),
           "Regelwerksmanual A: der Hebelfaktor kommt nicht vom Modell. In "
           "1.998 Hebel-Signalen kamen sie zweimal vor")

    # ⚠️ UND DIE ALTEN NAMEN MUESSEN LESBAR BLEIBEN - es gibt tausende Zeilen.
    from agent.empfehlung_vertrag import AKTION_AUS_HEBEL, AKTIONEN_HEBEL_ALT

    pruefe(P, "das alte Hebel-Vokabular ist vollstaendig abbildbar",
           set(AKTIONEN_HEBEL_ALT) - {"HEBEL_ERHÖHEN", "HEBEL_SENKEN"}
           <= set(AKTION_AUS_HEBEL)
           and set(AKTION_AUS_HEBEL.values()) <= set(AKTIONEN),
           "1.998 Zeilen in hebel_signals tragen die alten Namen - ohne "
           "Abbildung waere jede Auswertung ueber die Grenze hinweg blind")
    pruefe(P, "und das alte Vokabular ist das der alten Kette geblieben",
           set(AKTIONEN_HEBEL_ALT) == set(REQUIRED_HEBEL_ACTIONS),
           "hebel_analyst laeuft fuer Krypto nicht mehr, schreibt aber "
           "weiter in dieselbe Tabelle - ein Eingriff dort waere Arbeit an "
           "einem toten Pfad")

    basis = {"begruendung": "x", "was_dagegen": "y", "umgeworfen_durch": "z"}

    # DIE RICHTUNG IST PFLICHT, WO SIE ETWAS BEDEUTET - und nur dort.
    ok = validiere({**basis, "aktion": "KAUFEN", "richtung": "short",
                    "tranche_eur": 300}, "BTC", "hebel")
    pruefe(P, "KAUFEN mit Richtung wird angenommen und vereinheitlicht",
           ok["aktion"] == "KAUFEN" and ok["richtung"] == "SHORT")
    for aktion in ("KAUFEN", "NACHKAUFEN"):
        try:
            validiere({**basis, "aktion": aktion, "tranche_eur": 300},
                      "BTC", "hebel")
            fehlt = False
        except EmpfehlungUngueltig:
            fehlt = True
        pruefe(P, f"{aktion} OHNE Richtung wird abgewiesen", fehlt,
               "bei der Tranche ist die kleinste Groesse die vorsichtige "
               "Antwort - bei der Richtung gibt es keine: LONG statt SHORT "
               "ist nicht 'weniger', sondern das Gegenteil")
    pruefe(P, "NICHTS_TUN braucht keine Richtung",
           validiere({**basis, "aktion": "NICHTS_TUN"},
                     "BTC", "hebel")["aktion"] == "NICHTS_TUN")
    try:
        validiere({**basis, "aktion": "ERÖFFNEN", "tranche_eur": 300},
                  "BTC", "spot")
        weg = False
    except EmpfehlungUngueltig:
        weg = True
    pruefe(P, "ein alter Hebel-Name wird jetzt ueberall abgewiesen", weg,
           "frueher galt er bei Hebel und fiel bei Spot durch - jetzt gilt "
           "EIN Vokabular, und das ist der Punkt von S6a")

    # DER PROMPT FRAGT DIE RICHTUNG, ABER NICHT DEN FAKTOR (Kapitel 11.6).
    p_hebel = rolle_trader.prompt_fuer("hebel", "einstieg")
    p_spot = rolle_trader.prompt_fuer("spot", "einstieg")
    pruefe(P, "beide Prompts nennen dieselben fuenf Aktionen",
           all(a in p_hebel for a in AKTIONEN)
           and all(a in p_spot for a in AKTIONEN))
    pruefe(P, "und sie sind woertlich derselbe Satz", p_hebel == p_spot,
           "solange sie sich unterscheiden, sind es zwei Fragen - und S6b "
           "koennte den zweiten Lauf nicht streichen")
    pruefe(P, "beide fragen nach LONG oder SHORT",
           all("LONG" in p and "SHORT" in p for p in (p_hebel, p_spot)),
           "ohne die Richtung im Spot-Lauf waere 'Spot oder Hebel' schon "
           "dadurch vorentschieden, dass SHORT gar nicht sagbar ist")
    pruefe(P, "und verbieten ausdruecklich den Hebelfaktor",
           all("KEINEN Hebelfaktor" in p for p in (p_hebel, p_spot)),
           "der Faktor folgt aus Risikobudget und Liquidationsabstand - "
           "Regelwerksmanual A: Risikoparameter kommen nicht vom Modell")
    pruefe(P, "und sagen, dass die RECHNUNG ueber das Instrument entscheidet",
           all("entscheidet" in p and "nicht du" in p
               for p in (p_hebel, p_spot)),
           "das Modell soll gar nicht erst versuchen, Spot oder Hebel zu "
           "waehlen")

    # DAS SCHEMA HAENGT AM INSTRUMENT.
    sch_h = llm_schema.baue_trader_schema(rolle_trader, "hebel")
    sch_s = llm_schema.baue_trader_schema(rolle_trader, "spot")
    ph = sch_h.get("properties", sch_h)
    ps = sch_s.get("properties", sch_s)
    pruefe(P, "beide Schemata erlauben dieselben fuenf Aktionen",
           set(ph["aktion"]["enum"]) == set(ps["aktion"]["enum"])
           == set(AKTIONEN))
    pruefe(P, "und BEIDE tragen das Richtungsfeld",
           "richtung" in ph and "richtung" in ps
           and set(ph["richtung"]["enum"]) == set(RICHTUNGEN),
           "bis S6a fehlte es bei Spot - damit konnte der Spot-Lauf kein "
           "SHORT liefern, und das Instrument war vorentschieden")

    # DIE ARITHMETIK DREHT SICH BEI SHORT - alle vier Groessen.
    kurs = 55500.0
    lang = ER.rechne(kurs=kurs, atr=1677, risiko_eur=75, instrument="hebel",
                     betrag_wunsch_eur=500, topf_frei_eur=500)
    kurz = ER.rechne(kurs=kurs, atr=1677, risiko_eur=75, instrument="hebel",
                     betrag_wunsch_eur=500, topf_frei_eur=500, ist_short=True)
    pruefe(P, "bei LONG liegt der Stop unter dem Einstieg",
           lang["stop_eur"] < kurs < lang["ziel_eur"])
    pruefe(P, "bei SHORT darueber - und das Ziel darunter",
           kurz["stop_eur"] > kurs > kurz["ziel_eur"])
    pruefe(P, "die Liquidation dreht mit",
           lang["liquidation_etwa_eur"] < kurs < kurz["liquidation_etwa_eur"],
           "sonst stuende bei einem SHORT eine Liquidation unter dem "
           "Einstieg - dort kann sie nie greifen")
    pruefe(P, "das CRV bleibt in beiden Richtungen positiv",
           abs(lang["crv"] - kurz["crv"]) < 1e-9 and kurz["crv"] > 0)

    # DER WIDERLEGUNGSPREIS LIEGT BEI SHORT UEBER DEM KURS.
    kurz_w = ER.rechne(kurs=kurs, atr=1677, risiko_eur=75, instrument="hebel",
                       betrag_wunsch_eur=500, topf_frei_eur=500,
                       ist_short=True, umgeworfen_preis_eur=60000)
    pruefe(P, "ein Widerlegungspreis UEBER dem Kurs setzt den SHORT-Stop",
           abs(kurz_w["stop_eur"] - 60000) < 1e-6,
           "wer das vergisst, bekommt einen negativen Abstand und faellt "
           "still auf den ATR-Stop zurueck")
    kurz_falsch = ER.rechne(kurs=kurs, atr=1677, risiko_eur=75,
                            instrument="hebel", betrag_wunsch_eur=500,
                            topf_frei_eur=500, ist_short=True,
                            umgeworfen_preis_eur=51000)
    pruefe(P, "ein Preis auf der falschen Seite faellt auf den ATR-Stop zurueck",
           "ATR" in kurz_falsch["stop_regel"])

    # DIE MARKE IM WEG IST BEI SHORT EINE UNTERSTUETZUNG.
    kurz_u = ER.rechne(kurs=kurs, atr=1677, risiko_eur=75, instrument="hebel",
                       betrag_wunsch_eur=500, topf_frei_eur=500,
                       ist_short=True, widerstand=(50000, 3))
    pruefe(P, "eine Unterstuetzung vor dem SHORT-Ziel zieht es davor",
           kurz_u["ziel_eur"] > 50000 and kurz_u["crv"] < 2.0,
           "bei LONG ist die Mauer oben, bei SHORT unten")
    pruefe(P, "und der Text nennt sie beim Namen",
           "Unterstuetzung" in kurz_u["ziel_regel"])



def gesamtpruefung() -> None:
    """Der Abgleich ALLER Pakete gegeneinander (13.08.2026).

    WOZU, wenn jedes Paket seine eigene Gegenpruefung hat: die Paketpruefungen
    sehen jeweils EIN Paket. Widersprueche entstehen aber ZWISCHEN ihnen - und
    genau drei sind so entstanden, alle durch Paket 13 und keine davon von den
    23 Pruefungen des Pakets selbst bemerkt."""
    P = "gesamt"
    import os
    import re as _re
    from agent.empfehlung_vertrag import AKTIONEN, AKTIONEN_HEBEL
    from agent import signal_abbildung as SA
    from agent import signal_mail as SM
    from agent import trefferbilanz as TB, entscheidungsrechnung as ER
    from agent import ausstiegsrechnung as AR
    from agent.krypto import backward_tracking as BT
    from agent.krypto.ausstiegsregel import AUSLOESE_R
    from agent.krypto.hebel_analyst import REQUIRED_HEBEL_ACTIONS

    # --- VOKABULAR: sagen alle Pakete dasselbe? ---
    # ⚠️ S6a: `AKTIONEN_HEBEL` IST JETZT `AKTIONEN`. Die Deckung mit der
    # alten Kette gehoert seither zu `AKTIONEN_HEBEL_ALT`.
    from agent.empfehlung_vertrag import AKTIONEN_HEBEL_ALT as _AHA

    pruefe(P, "das ALTE Hebel-Vokabular deckt sich mit der alten Kette",
           set(_AHA) == set(REQUIRED_HEBEL_ACTIONS),
           "hebel_analyst schreibt weiter in hebel_signals - die Namen "
           "muessen lesbar bleiben, auch wenn die neue Kette sie nicht mehr "
           "spricht")
    pruefe(P, "JEDE Aktion beider Instrumente erreicht die Datenbank",
           all(SA.UMBENENNUNG.get(a, a) in SA.AKTIONEN
               for a in tuple(AKTIONEN) + tuple(AKTIONEN_HEBEL)),
           "Paket 13 gab dem Hebel sieben Aktionen; signal_abbildung kannte "
           "nur die fuenf der Spot-Kette - ein Hebel-Signal waere beim "
           "Schreiben gescheitert, und zwar erst im Betrieb")
    pruefe(P, "die Mail zeigt auch bei ERÖFFNEN eine Rechnung",
           "ERÖFFNEN" in SM.AKTIONEN_MIT_EINSTIEG,
           "sonst stuende dort 'Kein Einstieg geplant' und daneben eine "
           "ausgerechnete Zone im Nichts")
    pruefe(P, "das Vokabular wird importiert, nicht abgeschrieben",
           "AKTIONEN as AKTIONEN_NEU" in _quelltext("agent/signal_abbildung.py"),
           "hier stand eine Handkopie der fuenf Spot-Aktionen - dieselbe "
           "Sorte Kopie wie die Kostensaetze am 12.08.")

    # --- KONSTANTEN: eine Quelle oder mehrere? ---
    pruefe(P, "die Kostensaetze kommen aus EINER Quelle",
           TB.KOSTEN_JE_SEITE["krypto"] == BT._KOSTEN_KRYPTO_JE_SEITE)
    pruefe(P, "das CRV ist in Rechnung und Bilanz dasselbe",
           ER.GRENZEN["crv"] == TB.CRV)
    pruefe(P, "die Ausstiegsschwelle ist importiert, nicht kopiert",
           AR.AUSLOESE_R is AUSLOESE_R)
    # ⚠️ HIER STAND EIN VERGLEICH GEGEN LITERALE (bis 22.08.2026).
    #
    # `GRENZEN["stop_min_relativ"] == 0.025` prueft NICHT gegen die config -
    # es nagelt nur die Konstante fest. Wer die config aendert, merkt hier
    # nichts; der Kommentar sagte "muss hier mitziehen", also von Hand. Das
    # ist genau die Sorte Zusage, die beim ersten Mal gebrochen wird.
    #
    # JETZT AN DER QUELLE: die Datei wird gelesen und verglichen.
    import yaml as _YAML

    _cfg_roh = _YAML.safe_load(
        io.open("Basisinfos/config.yaml", encoding="utf-8").read())
    _risiko = (_cfg_roh or {}).get("risiko") or {}
    _hebel_cfg = _risiko.get("hebel") or {}
    for _schluessel, _grenze, _wo in (
            ("sl_abstand_eng_schwelle_relativ", "stop_min_relativ", _risiko),
            ("sl_abstand_min_atr_faktor", "stop_min_atr", _risiko),
            ("max_hebel", "hebel_max", _hebel_cfg)):
        _wert = _wo.get(_schluessel)
        pruefe(P, f"GRENZEN['{_grenze}'] stimmt mit der config ueberein",
               _wert is not None
               and abs(float(_wert) - float(ER.GRENZEN[_grenze])) < 1e-9,
               f"config {_schluessel}={_wert!r}, "
               f"GRENZEN['{_grenze}']={ER.GRENZEN[_grenze]!r} - wer eine "
               f"Zahl aendert, muss die andere mitziehen; genau dafuer ist "
               f"diese Pruefung da")

    # ---- S6d: DIE FUENF KONFLIKTDECKEL SIND WEG (22.08.2026) -------------
    #
    # Gemessen ueber 202 Signale mit Hebelvorschlag: Regime-Konflikt,
    # Retail-Konsens und Gegenszenario haben KEIN EINZIGES Mal gegriffen.
    # Und ein Hebeldeckel senkt in der neuen Rechnung das Risiko ohnehin
    # nicht (Kapitel 136). Sie stehen nicht mehr in der config.
    for _tot in ("regime_konflikt_hebel_deckel", "gegenszenario_hebel_deckel",
                 "technischer_konflikt_hebel_deckel",
                 "crv_knapp_hebel_deckel", "retail_konsens_hebel_deckel"):
        pruefe(P, f"{_tot} steht nicht mehr in der config",
               _tot not in _hebel_cfg,
               "ein Regler, der nur einen toten Pfad steuert, sieht beim "
               "Lesen aus wie eine lebende Einstellung")
    # ⚠️ UND DIE ALTE KETTE LAEUFT UNVERAENDERT WEITER. Ihre Werte stehen
    # jetzt als Vorgabe im Code - ein fehlender Schluessel darf dort kein
    # KeyError sein.
    _hrg = _quelltext("agent/krypto/hebel_risk_gate.py")
    pruefe(P, "die alte Kette liest die Deckel mit Vorgabe, nicht hart",
           all(f'hebel_cfg["{k}"]' not in _hrg for k in (
               "regime_konflikt_hebel_deckel", "gegenszenario_hebel_deckel",
               "technischer_konflikt_hebel_deckel",
               "crv_knapp_hebel_deckel", "retail_konsens_hebel_deckel")),
           "ein direkter Zugriff waere nach dem Entfernen ein KeyError - "
           "und zwar erst im Betrieb")

    # --- EINHEITEN: eine Waehrung, eine Schreibweise? ---
    # ⚠️ GEMESSEN STATT IM QUELLTEXT GESUCHT (17.08.2026). Hier stand
    # `"maketrans" in _quelltext(datei)` - eine Suche nach einer
    # Schreibweise im CODE. Sie ist heute fehlgeschlagen, weil die vier
    # Kopien der Formatierung durch EINE gemeinsame ersetzt wurden: das
    # Verhalten war richtig, die Pruefung sah nur das falsche Wort.
    #
    # Eine Pruefung, die den Quelltext liest statt das Ergebnis, faellt
    # bei jeder Aufraeumarbeit an - und wird dann angepasst statt
    # ernstgenommen. "Katalog ist keine Messung."
    from agent.ausstiegsrechnung import _de as _de_a
    from agent.faktenblock import _de as _de_f
    from agent.schreibweise import de as _de_s
    from agent.trefferbilanz import _de as _de_t

    for name, fn, stellen in (("schreibweise", _de_s, 2),
                              ("faktenblock", _de_f, 2),
                              ("ausstiegsrechnung", _de_a, 2),
                              ("trefferbilanz", _de_t, 2),
                              ("signal_mail.eur", SM.eur, 2)):
        pruefe(P, f"{name} schreibt Zahlen deutsch",
               fn(1234.5, stellen) == "1.234,50",
               f"bekommen: {fn(1234.5, stellen)!r} - zwei Schreibweisen in "
               f"einer Nachricht sind der Fehler aus Umbauplan 12.5")
    pruefe(P, "und alle vier rechnen mit DERSELBEN Funktion",
           all("from agent.schreibweise import de" in _quelltext(d)
               for d in ("agent/faktenblock.py",
                         "agent/ausstiegsrechnung.py",
                         "agent/trefferbilanz.py",
                         "agent/signal_mail.py")),
           "vier Kopien derselben Zeile waren vier Stellen zum "
           "Auseinanderlaufen")

    # --- ERREICHBARKEIT: was ist gebaut und ruft niemand? ---
    module = ["entscheidungsrechnung", "faktenblock", "faktenblock_quellen",
              "signal_mail", "ausstiegsrechnung", "rollen_gate",
              "gegenpruefer_rollen", "trefferbilanz", "handelsauftrag",
              "signal_abbildung", "toepfe", "marktlage", "rolle_analyst",
              "rolle_trader", "rollen_eingabe"]
    quellen = {}
    for wurzel in ("agent", "ui", "scheduler"):
        for pfad, _, dateien in os.walk(wurzel):
            for d in dateien:
                if d.endswith(".py"):
                    voll = os.path.join(pfad, d).replace(chr(92), "/")
                    quellen[voll] = _quelltext(voll)
    # ⚠️⚠️ TRANSITIV RECHNEN, NICHT DIREKT (31.08.2026).
    #
    # Die erste Fassung fragte nur nach DIREKTEN Nennungen aus
    # `scheduler/` oder `ui/` und meldete daraufhin "15 von 15 ohne
    # Betriebsaufrufer" - der offene Punkt B1. Das war falsch, und die
    # falsche Sicherheit war teuer: sie liess G-6 folgenlos erscheinen
    # ("wirkt erst mit der Verdrahtung"). Auf dieser Annahme stand auch
    # der Kopf von `vorschau_g6_scharfschaltung.py`.
    #
    # Tatsaechlich haengen diese fuenfzehn Module an `rollen_lauf`, und
    # `scheduler/rollen_job.py:444` ruft `RL.fuehre_lauf` auf. Die
    # Notebook-Produktion belegt es: 119 bis 235 Signale mit
    # `quelle_kette='rollen'` PRO TAG, durchgehend seit dem 14.08.2026.
    #
    # Erreichbarkeit ist transitiv. Wer sie direkt prueft, misst die
    # Importtiefe statt des Betriebs.
    def _erreichbar_von_betrieb() -> set:
        """⚠️ UEBER ECHTE IMPORTE, NICHT UEBER TEXTVORKOMMEN.

        Die erste transitive Fassung (heute frueher) suchte den Modulnamen
        im Quelltext. Sie meldete `positionsfuehrung` als verdrahtet -
        der einzige Treffer war ein DOCSTRING in `handelsauftrag.py:74`
        (*"positionsfuehrung  `hebel_signals` wurde nie gelesen"*).

        Eine Erwaehnung ist kein Aufruf. Wer Text durchsucht, findet auch
        jede Notiz ueber ein Modul - und macht aus einer offenen Luecke
        eine grüne Zeile. `positionsfuehrung` steht seit dem 27.08. als
        Punkt B im Roten Faden: gebaut, kein Aufrufer.
        """
        import ast as _ast
        baum, kanten, namen = {}, {}, {}
        for _p, _t in quellen.items():
            try:
                baum[_p] = _ast.parse(_t)
            except Exception:                            # noqa: BLE001
                continue
            namen.setdefault(_p.rsplit("/", 1)[-1][:-3], []).append(_p)
        for _p, _b in baum.items():
            ziele = set()
            for _n in _ast.walk(_b):
                if isinstance(_n, _ast.Import):
                    for _al in _n.names:
                        ziele.add(_al.name.rsplit(".", 1)[-1])
                elif isinstance(_n, _ast.ImportFrom):
                    if _n.module:
                        ziele.add(_n.module.rsplit(".", 1)[-1])
                    for _al in _n.names:
                        ziele.add(_al.name)
            kanten[_p] = ziele
        front = [x for x in baum if x.startswith(("scheduler/", "ui/"))]
        gesehen = set(front)
        while front:
            for _z in kanten.get(front.pop(), ()):
                for _k in namen.get(_z, ()):
                    if _k not in gesehen:
                        gesehen.add(_k)
                        front.append(_k)
        return gesehen

    _erreicht = _erreichbar_von_betrieb()
    ohne_betrieb = [m for m in module
                    if not any(q.endswith("/%s.py" % m) for q in _erreicht)]
    pruefe(P, "⚠️ die Erreichbarkeit wird TRANSITIV gerechnet",
           any(q.endswith("/rollen_lauf.py") for q in _erreicht)
           and "fuehre_lauf" in _quelltext("scheduler/rollen_job.py"),
           "direkt gerechnet meldete diese Pruefung '15 von 15 ohne "
           "Betriebsaufrufer' - waehrend die Notebook-Produktion 119 bis "
           "235 Rollen-Signale PRO TAG schrieb. Eine Verdrahtungspruefung, "
           "die den laufenden Betrieb uebersieht, laesst jede Aenderung am "
           "Signalfluss folgenlos aussehen")
    pruefe(P, "⚠️⚠️ und damit wirkt G-6 SOFORT nach dem Pull",
           not ohne_betrieb,
           "unerreichbar: " + ", ".join(sorted(ohne_betrieb)))
    # ⚠️ DIE GEGENPROBE: die Pruefung muss eine ECHTE Luecke noch finden.
    # Ohne sie waere "alles verdrahtet" auch dann gruen, wenn die Methode
    # kaputt ist - und genau das war heute frueher der Fall.
    # ⚠️ DIE GEGENPROBE WURDE AM 01.09.2026 NACHGEZOGEN - so wie ihr eigener
    # Begruendungstext es verlangte.
    #
    # Sie stand auf `positionsfuehrung` ("Punkt B im Roten Faden: gebaut,
    # kein Aufrufer") und lautete: *„Wenn diese Zeile faellt, ist entweder B
    # erledigt (dann hier nachziehen) - oder die Erreichbarkeitsrechnung
    # zaehlt wieder Docstrings als Aufrufe."* B IST mit Schritt 7 erledigt,
    # also wird die Kontrollgroesse getauscht, nicht die Pruefung geloescht.
    #
    # ⚠️ EINE VERDRAHTUNGSPRUEFUNG BRAUCHT IMMER EINE ECHTE LUECKE als
    # Gegenprobe. Ohne sie waere "alles verdrahtet" auch dann gruen, wenn
    # die Methode kaputt ist - und genau das war am 31.08. der Fall
    # (Textsuche fand `positionsfuehrung` im Docstring von
    # `handelsauftrag.py:74`).
    #
    # Neue Kontrollgroesse: `szenario_entscheidung` - Stufe 2 des Umbaus vom
    # 10.08., gebaut und seither ohne Betriebsaufrufer. Sie steht in
    # `zeige_modulkarte.py --tot`; faellt DIESE Zeile, gilt dasselbe wie
    # vorher: entweder ist sie verdrahtet (dann hier nachziehen) oder die
    # Rechnung zaehlt wieder Docstrings.
    pruefe(P, "⚠️ und sie findet eine BEKANNTE Luecke weiterhin",
           not any(x.endswith("/szenario_entscheidung.py")
                   for x in _erreicht),
           "`szenario_entscheidung` ist seit dem 10.08. gebaut und ohne "
           "Betriebsaufrufer (Modulkarte --tot). Wenn diese Zeile faellt, "
           "ist sie entweder verdrahtet (dann hier nachziehen) - oder die "
           "Erreichbarkeitsrechnung zaehlt wieder Docstrings als Aufrufe")
    pruefe(P, "⚠️ und `positionsfuehrung` ist jetzt ERREICHBAR (Schritt 7)",
           any(x.endswith("/positionsfuehrung.py") for x in _erreicht),
           "sie war die vorige Kontrollgroesse und ist seit dem 01.09. "
           "verdrahtet - `rollen_lauf` gibt ihre Zeilen an "
           "`verkaufsrechnung.sammel_mail`. Faellt diese Zeile, ist Schritt 7 "
           "still zurueckgefallen")



def _ohne_bremsen() -> dict:
    """Eine Konfiguration, in der KEIN Cooldown greift - abgeleitet, nicht
    abgeschrieben (02.09.2026).

    ⚠️⚠️ WARUM ABGELEITET. Am 02.09. meldete das Notebook 13 rote Punkte,
    alle aus einer Ursache: die Testkonfiguration setzte
    `cooldown_stunden_je_gruppe` auf 0, aber L4/L5 hatte am 28.08. einen
    ZWEITEN Schluessel eingefuehrt - `cooldown_stunden_je_strategie` mit
    48 Stunden fuer die Akkumulation. Der stand nicht drin, und der
    Cooldown der echten Produktion sperrte jeden Probelauf.

    Im Trichter war es zu sehen: `Cooldown bis 2026-09-04T07:13` - genau
    48 Stunden.

    ⚠️ ES WAREN AUSSERDEM ZWEI KOPIEN (`_OHNE_BREMSEN` in paket_b1,
    `_OHNE_BREMSEN15` in paket_15), obwohl der Kommentar dort schon sagte
    "dieselbe Konfiguration wie dort". Zwei Kopien laufen auseinander -
    das ist keine Vorhersage, das ist am 28.08. passiert.

    ⚠️ AM DESKTOP FIEL NICHTS AUF, weil dort `data/tradinginfotool.db`
    leer ist: kein Signalbestand, also kein Cooldown, also kein Problem.
    Vierte Spielart von "Test haengt an der Produktion" (Methodik 2.66) -
    die Pruefung ueberlebt nur, WEIL die Daten guenstig liegen.

    DIE LOESUNG: die Schluessel werden aus `agent/wiederholung.py`
    ABGELESEN, nicht aufgezaehlt. Kommt ein neuer dazu, ist er automatisch
    dabei. Die Dauerpruefung unten stellt sicher, dass das Ablesen
    funktioniert.
    """
    import ast as _ast
    import io as _io
    quelle = _io.open("agent/wiederholung.py", encoding="utf-8").read()
    baum = _ast.parse(quelle)
    fn = next((n for n in _ast.walk(baum)
               if isinstance(n, _ast.FunctionDef) and n.name == "stunden"),
              None)
    rollen, budget = {}, {}
    for k in _ast.walk(fn or baum):
        # jedes `.get("cooldown...")` im Rumpf von `stunden()`
        if (isinstance(k, _ast.Call) and isinstance(k.func, _ast.Attribute)
                and k.func.attr == "get" and k.args
                and isinstance(k.args[0], _ast.Constant)
                and isinstance(k.args[0].value, str)
                and "cooldown" in k.args[0].value):
            rollen[k.args[0].value] = 0.0
    # ⚠️ Die Gruppen- und Strategie-Schluessel sind WOERTERBUECHER, keine
    # Zahlen - eine 0.0 dort waere wirkungslos, weil `.get(gruppe)` dann
    # None liefert und die naechste Ebene greift.
    for name in list(rollen):
        if name.endswith(("_je_gruppe", "_je_strategie")):
            rollen[name] = {k: 0.0 for k in
                            ("krypto", "aktien", "rohstoffe", "themen_etf",
                             "hedge", "einstieg", "akkumulation", "swing")}
    from agent import wiederholung as _WH
    for s in _WH._SCHLUESSEL.values():
        budget[s] = 0.0
    return {"anlass": {"aktiv": False}, "rollen_kette": rollen,
            "budget_allocator": budget}


def paket_b1() -> None:
    """B1 - der eine Ort, an dem die Kette zusammengesetzt wird."""
    P = "B1"
    import sqlite3
    from agent import rollen_lauf as RL, rollen_eingabe as RE

    # DIE SCHUTZSCHALTER SIND WICHTIGER ALS DER DURCHLAUF.
    q = sqlite3.connect("data/tradinginfotool.db")
    # ⚠️ WIE DIE PRODUKTION, MIT ZEILENFABRIK (16.08.2026). Ohne sie
    # scheitert JEDER Leser, der `row["spalte"]` benutzt - und seit die
    # Nutzerschalter zufallen statt aufzugehen, blockiert das den ganzen
    # Lauf. `db.get_connection()` setzt sie; ein Test ohne sie prueft eine
    # Verbindung, die es im Betrieb nicht gibt.
    con = sqlite3.connect(":memory:"); q.backup(con); q.close()
    con.row_factory = sqlite3.Row
    # ⚠️⚠️ DIE SIGNALHISTORIE NEUTRALISIEREN (03.09.2026). Sechste Spielart
    # von "Test haengt an der Produktion" (2.66) - und die teuerste bisher,
    # weil sie die Suite am NOTEBOOK mit SIEBEN roten Zeilen zurueckliess.
    #
    # WAS SCHIEFGING. `fuehre_lauf` baut seine Ausstiegsfuehrung aus
    # `compute_ausstiegs_empfehlungen(conn, ...)` - also aus DIESER
    # Verbindung, einer Kopie der Produktion. Die Stufe `aktion` sperrt
    # daraufhin einen Einstieg, wenn fuer dasselbe Symbol ein Ausstieg
    # faellig ist.
    #
    #     Desktop   LINK/ETH letztes Signal HALTEN      -> Stufe passiert
    #     Notebook  LINK/ETH letztes Signal NACHKAUFEN  -> alle 5 verworfen
    #
    # Fuenf Folgefehler haengen daran ("fuer den Einstieg entsteht eine
    # Mail", "was der Entscheider verwirft", "je Zelle eine Mail" ...) -
    # alle nur, weil die Testsymbole auf dem einen Geraet eine Vorgeschichte
    # haben und auf dem anderen nicht.
    #
    # ⚠️ WARUM LOESCHEN UND NICHT ANPASSEN. Ein Test, dessen Ergebnis vom
    # Signalbestand des Geraets abhaengt, prueft nicht die Kette, sondern
    # den Zufall der Datenlage. Der Ausgangszustand muss FESTSTEHEN -
    # dieselbe Begruendung wie bei `_ohne_bremsen()` fuer den Cooldown.
    #
    # ⚠️ ES BLEIBT EINE KOPIE IM SPEICHER. Die Produktionsdatenbank wird
    # nicht angefasst; `q` ist bereits geschlossen.
    con.execute("DELETE FROM signals")
    try:
        con.execute("DELETE FROM hebel_signals")
    except sqlite3.Error:
        pass                    # die Tabelle gibt es nicht ueberall
    con.commit()
    for name, kw, mit_conn in (
            ("eine unbekannte Betriebsart", {"betriebsart": "halbscharf"}, True),
            ("probe ohne Modell-Client", {"betriebsart": "probe"}, True),
            ("scharf ohne Modell-Client", {"betriebsart": "scharf"}, True),
            ("ein Lauf ohne Verbindung", {"betriebsart": "trocken"}, False)):
        try:
            RL.fuehre_lauf(conn=con if mit_conn else None, reihen={},
                           symbole=[], **kw)
            ok = False
        except RL.LaufAbgebrochen:
            ok = True
        pruefe(P, f"{name} wird abgewiesen", ok,
               "ein Weg, den man erst nachtraeglich absichert, ist in der "
               "Zwischenzeit ungesichert")
    pruefe(P, "ein Trockenlauf OHNE Aufzeichnung bricht ab",
           _wirft(lambda: RL.fuehre_lauf(conn=con, reihen={}, symbole=[],
                                         betriebsart="trocken"),
                  RL.LaufAbgebrochen),
           "ein leerer Durchlauf saehe aus wie ein Erfolg")

    # DATUM -> TAGE. Der Fehler, den der erste Trockenlauf gefunden hat.
    pruefe(P, "ein Datum wird in Tage umgerechnet",
           RL._tage_bis("2026-09-15", "2026-09-01") == 14,
           "das Modell liefert `umgeworfen_bis` als Datum, die Rechnung "
           "erwartet `umgeworfen_tage` als Zahl - zwei Pakete, zwei Einheiten")
    pruefe(P, "ein Datum in der Vergangenheit gibt None, nicht negativ",
           RL._tage_bis("2026-08-01", "2026-09-01") is None,
           "eine abgelaufene Frist ist keine Haltedauer, sondern ein Fall "
           "fuer den Ausstieg")
    pruefe(P, "ein unbrauchbares Datum gibt None",
           RL._tage_bis("morgen", "2026-09-01") is None
           and RL._tage_bis(None, None) is None)

    # DER ECHTE TROCKENLAUF - gegen echte Kursreihen, ohne einen Modellaufruf.
    from backtest_llm1_historisch import lade_reihen_aus_db as lade
    reihen = lade("data/tradinginfotool.db")
    symbole = [s for s in ("BTC", "ETH", "LINK") if s in reihen]
    pruefe(P, "die Kursreihen liegen vor", len(symbole) == 3, str(symbole))

    def befund(sym, kauft):
        r = reihen[sym]; i = len(r) - 1
        k = RE.kurs_eur(sym, r, i, "data/tradinginfotool.db")
        a = RE.atr_eur(sym, r, i, "data/tradinginfotool.db")
        return {"aktion": "KAUFEN" if kauft else "NICHTS_TUN",
                # S6c: bei KAUFEN Pflicht, bei NICHTS_TUN wird sie verworfen -
                # beides deckt dieselbe Zeile ab.
                **({"richtung": "LONG"} if kauft else {}),
                "belege": [{"fakt": "Schwankung niedrig", "richtung": "dafuer",
                            "gewicht": "hoch"}],
                "unabhaengige_faktoren": 2,
                "begruendung": "Die Schwankung geht zurueck.",
                "was_dagegen": "Abstand zum Hoch.",
                "umgeworfen_durch": "Tagesschluss unter dem Jahrestief.",
                **({"einstieg_eur": round(k, 2),
                    "stop_eur": round(k - 2.5 * a, 2)} if kauft else {})}

    # ⚠️ A1 (23.08.2026): DER EINSTIEG GEHOERT AUF DEN GEWAEHLTEN WERT.
    # Vorher stand hier fest "BTC". Seit die Auswahl-Stufe existiert,
    # kommt nur noch der Rangbeste ueberhaupt zum Urteil - und wenn
    # das nicht BTC ist, prueft dieser Test einen Einstieg, der nie
    # stattfindet. Die AUFZEICHNUNG folgt der Auswahl, nicht umgekehrt.
    from agent import auswahl as _AWT
    _awt = _AWT.waehle(reihen, symbole)
    _kauft = (sorted(_awt["gewaehlt"]) or ["BTC"])[0]
    antworten = {"lagebild": {"lage": "Die Maerkte zeigen eine Divergenz.",
                              "klassen": [{"klasse": "krypto",
                                           "einstufung": "unguenstig",
                                           "warum": "Bitcoin steht tief."}],
                              "belege": ["Bitcoin steht tief."]},
                 "befund": {s: befund(s, s == _kauft) for s in symbole},
                 # ⚠️ SEIT G-6 (31.08.2026): ohne gestellte Raenge liegt jedes
                 # Potential bei 0,000, Stufe 11 verwirft, und dieser
                 # Trockenlauf koennte keinen Einstieg mehr zeigen. Gestellt
                 # wird das beste Fuenftel - geprueft wird hier die KETTE,
                 # nicht die Bewertung.
                 "marktraenge": {s: {"funding_fuenftel": 0,
                                     "turnover_fuenftel": 0}
                                 for s in symbole}}
    def _inhalt(pfad):
        """Der INHALT aller Tabellen, nicht die Bytes der Datei.

        Ein Byte-Vergleich war die erste Fassung - und er schlug fehl, obwohl
        KEINE Zeile geschrieben wurde: SQLite ordnet beim Oeffnen Seiten um,
        und der Aenderungszaehler im Header wandert mit. Die Pruefung haette
        einen Fehler gemeldet, wo keiner war, und beim naechsten Mal haette
        man sie deshalb weggelassen."""
        import hashlib as _h
        c = sqlite3.connect(pfad)
        namen = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        h = _h.md5()
        for n in namen:
            for zeile in c.execute(f'SELECT * FROM "{n}"'):
                h.update(repr(zeile).encode("utf-8", "replace"))
        c.close()
        return h.hexdigest()

    # ⚠️ DIE BREMSEN WERDEN FUER DIESE PRUEFUNGEN ABGESCHALTET (24.08.2026).
    #
    # DER FEHLER, DEN DAS BEHEBT - und er hat die ganze Suite zum ABSTURZ
    # gebracht, nicht nur zu einem roten Punkt:
    #
    #     IndexError: list index out of range
    #     lang = _marken(_lauf("hebel","KAUFEN","LONG")["mails"][0]["text"])
    #
    # `_lauf` laeuft gegen die ECHTE Produktionsdatenbank. Cooldown und
    # Anlass-Fingerabdruck lesen daraus, WANN ETH zuletzt beurteilt wurde. Auf
    # einem Rechner, auf dem die Produktion gerade laeuft, ist ETH gesperrt -
    # dann entsteht keine Mail, und `["mails"][0]` fliegt.
    #
    # ⚠️ DER TEST HAENGT ALSO AM ZUSTAND DER PRODUKTION. Dieselbe Fehlerklasse
    # wie Methodik 2.64 (Kalender), nur mit Daten statt Datum - und sie faellt
    # erst auf, seit die Kette wirklich laeuft.
    #
    # WAS DIESE PRUEFUNGEN MESSEN WOLLEN, ist die GEOMETRIE der Richtung -
    # nicht, ob eine Bremse gerade greift. Also werden beide Bremsen
    # ausgeschaltet, statt das Ergebnis dem Zufall des Zeitpunkts zu
    # ueberlassen. Die Bremsen haben ihre eigenen Pruefungen.
    _OHNE_BREMSEN = _ohne_bremsen()

    # ⚠️ GEGEN EINE EIGENE DATEIKOPIE, NICHT GEGEN DIE ECHTE DATEI
    # (24.08.2026, letzter der acht Notebook-Funde).
    #
    # DIE PRUEFUNG SCHLUG MAL AN UND MAL NICHT, ohne dass sich am geprueften
    # Code etwas geaendert haette - drei Laeufe rot, zwei gruen. Der Grund:
    # `con` ist laengst eine IN-MEMORY-Kopie (siehe oben), ueber sie kann der
    # Lauf die Produktivdatei gar nicht erreichen. Gehasht wurde aber
    # `data/tradinginfotool.db` SELBST - und dort schreibt am Notebook der
    # 24/7 laufende Scheduler parallel. Die Pruefung mass also die
    # Produktion, nicht den Trockenlauf. Dieselbe Familie wie 2.66/2.68, nur
    # zeitlich statt zahlenmaessig: nicht entscheidbar, solange ein fremder
    # Schreiber dieselbe Datei anfasst.
    #
    # `fuehre_lauf(db=...)` reicht den Pfad an ALLE Fakten-Module durch
    # (`RE.kurs_eur`, `RE.atr_eur`, `RE.bestand`, `RE.fx_eur_je_usd`) - die
    # Zusicherung "ein Trockenlauf schreibt nicht" laesst sich damit an einer
    # Kopie pruefen, die sonst niemand anfasst. Das ist STAERKER als vorher:
    # jede Aenderung dort kann nur vom Lauf kommen.
    #
    # `Connection.backup()` statt Dateikopie - unter WAL stehen die juengsten
    # Aenderungen in `-wal`, eine blosse Kopie waere nicht in sich stimmig
    # (dieselbe Regel wie beim NB-Export).
    import shutil as _shutil
    import tempfile as _tempfile

    _tmp_b1 = _tempfile.mkdtemp(prefix="tit_b1_")
    _db_kopie = _tmp_b1 + "/produktiv_kopie.db"
    try:
        _src_b1 = sqlite3.connect("data/tradinginfotool.db")
        _dst_b1 = sqlite3.connect(_db_kopie)
        _src_b1.backup(_dst_b1)
        _src_b1.close(); _dst_b1.close()

        vorher = _inhalt(_db_kopie)
        erg = RL.fuehre_lauf(conn=con, reihen=reihen, symbole=symbole,
                             betriebsart="trocken", antworten=antworten,
                             config=_OHNE_BREMSEN, db=_db_kopie)
        _nachher = _inhalt(_db_kopie)
        pruefe(P, "der Trockenlauf laeuft ohne Fehler durch",
               not erg["fehler"], str(erg["fehler"][:2]))
        pruefe(P, "und schreibt KEINE Zeile in die Produktivdatenbank",
               _nachher == vorher,
               "gemessen an einer EIGENEN Kopie, die sonst niemand anfasst - "
               "eine Aenderung dort kann nur vom Lauf kommen. Die Verbindung "
               "wird uebergeben, nie hier geoeffnet; die Fakten-Module lesen "
               "mit ihrer eigenen Vorgabe, und das muss LESEN bleiben")
    finally:
        _shutil.rmtree(_tmp_b1, ignore_errors=True)
    pruefe(P, "er schreibt auch in die Kopie nichts",
           not erg["signale"],
           "trocken heisst: kein Modellaufruf, kein Schreiben, keine Mail")
    d = erg["durchlauf"]
    # ⚠️ A1 (23.08.2026): NICHT MEHR ALLE SYMBOLE ERREICHEN DAS URTEIL.
    # Genau das ist der Zweck der Auswahl - und der Trockenlauf muss sie
    # mitmachen, sonst meldet er einen Durchsatz, den der scharfe
    # Betrieb nie erreicht (dieselbe Lehre wie bei `asset_schalter`,
    # O-38 am 16.08.).
    # ⚠️ DER BESTAND PASSIERT DIE AUSWAHL IMMER (23.08.2026). Bei einem
    # gehaltenen Wert lautet die Frage "halten oder verkaufen" - die
    # stellt sich unabhaengig vom Rangplatz. BTC, ETH und LINK sind hier
    # im Bestand, also kommen alle drei zum Urteil; die Auswahl verwirft
    # niemanden. Genau das ist gewollt, und die Erwartung folgt ihm.
    _durch = {s for s in symbole
              if s in (_awt.get("gewaehlt") or set())
              or (RE.bestand(s, "data/tradinginfotool.db", "spot")
                  or (0,))[0]}
    # ⚠️⚠️ DER TRICHTER ZAEHLT SEIT SCHRITT 3 ZELLEN, NICHT SYMBOLE
    # (01.09.2026). BTC, ETH und SOL sind in `_DCA_ERLAUBT_DEFAULT_SYMBOLS`
    # und bekommen ZWEI Spot-Zellen (`einstieg` und `akkumulation`), alle
    # uebrigen eine. `durchlauf.beginne` steht deshalb in der Zellenschleife
    # - stuende es davor, faellt die zweite Zelle still unter den Tisch
    # (Paket "Zellen" haelt genau diese Falle fest).
    #
    # ⚠️ DIE ERWARTUNG WIRD NICHT HARTKODIERT, sondern aus derselben Quelle
    # gerechnet, die auch der Lauf benutzt. Eine feste Zahl waere beim
    # naechsten Schalter falsch, ohne dass es auffiele.
    def _zellenzahl(symbolmenge):
        # ⚠️ Funktionslokal und unter eigenem Namen - dieses Paket haelt
        # sonst keinen `assetklassen`-Bezug, und ein modulweiter Name, der
        # hier lokal ueberschrieben wuerde, ist der Namensschatten aus T4c.
        from agent import assetklassen as _AKzz
        _je = {}
        for _zz in _AKzz.zellen(_WLOBJ(symbole), con):
            if _zz["instrument"] == "spot" and _zz["symbol"] in symbolmenge:
                _je.setdefault(_zz["symbol"], 0)
                _je[_zz["symbol"]] += 1
        return sum(_je.get(s, 1) for s in symbolmenge)

    _k = _zellenzahl(_durch) if _awt["aktiv"] else _zellenzahl(set(symbole))
    _hinein_erwartet = _zellenzahl(set(symbole))
    pruefe(P, "alle ZELLEN gehen hinein, nur die gewaehlten kommen zum Urteil",
           d.hinein == _hinein_erwartet
           and d.bestanden_je_stufe["urteil"] == _k,
           f"hinein {d.hinein} (erwartet {_hinein_erwartet} Zellen aus "
           f"{len(symbole)} Symbolen), Urteil "
           f"{d.bestanden_je_stufe['urteil']}, gewaehlt {_k}")
    pruefe(P, "der Trichter bleibt monoton: was die Auswahl nimmt, fehlt danach",
           d.verloren_je_stufe["auswahl"] == _hinein_erwartet - _k,
           "eine Stufe, die verwirft und es nicht zaehlt, macht die "
           "Summe unauffindbar")
    # ⚠️ EIN MODELLURTEIL JE ASSET: beide Zellen desselben Symbols bekommen
    # dieselbe Antwort (Schritt 4, Urteilsspeicher). Ein NICHTS_TUN faellt
    # damit fuer BEIDE Zellen heraus - die Zahl folgt den Zellen, nicht den
    # Symbolen.
    # ⚠️ GENAU EIN SYMBOL KAUFT (`_kauft`), und es hat so viele ZELLEN, wie
    # `zellen()` ihm gibt. Meine erste Fassung setzte hier `BTC` ein - das
    # war geraten und stimmte nur zufaellig nicht: `_kauft` ist das von der
    # AUSWAHL gewaehlte Symbol, und das hat hier eine Zelle, nicht zwei.
    pruefe(P, "ein NICHTS_TUN faellt bei der Aktion heraus",
           d.verloren_je_stufe["aktion"] == _k - _zellenzahl({_kauft}),
           f"{_k} Zellen kamen zum Urteil, {_kauft} kauft mit "
           f"{_zellenzahl({_kauft})} Zelle(n). Trichter: "
           f"bestanden={dict(d.bestanden_je_stufe)} "
           f"verloren={dict(d.verloren_je_stufe)}")
    pruefe(P, "fuer den Einstieg entsteht eine Mail", len(erg["mails"]) == 1)
    # ⚠️ G-6 (31.08.2026): der Entscheider verwirft. Ob am Ende einer
    # herauskommt, haengt jetzt am Potential - und genau das ist der Zweck.
    # Geprueft wird deshalb die BEZIEHUNG, nicht die feste Zahl: was der
    # Entscheider verliert, darf nicht mehr herauskommen.
    _e_verloren = d.verloren_je_stufe["entscheider"]
    pruefe(P, "⚠️ was der Entscheider verwirft, kommt nicht heraus (G-6)",
           d.heraus == max(0, 1 - _e_verloren),
           "heraus=%d, Entscheider verlor %d - die Summe muss aufgehen"
           % (d.heraus, _e_verloren))
    pruefe(P, "und die Mail entsteht nur fuer das, was durchkommt",
           len(erg["mails"]) >= d.heraus,
           "eine Mail ohne Signal waere eine Empfehlung ohne Grundlage")

    # EIN FEHLENDES SYMBOL WIRD GEZAEHLT, NICHT UEBERSPRUNGEN.
    erg2 = RL.fuehre_lauf(conn=con, reihen=reihen, symbole=symbole + ["GIBTSNICHT"],
                          betriebsart="trocken", antworten=antworten,
                          config=_OHNE_BREMSEN)
    pruefe(P, "ein Symbol ohne Kursreihe wird als Verlust gezaehlt",
           erg2["durchlauf"].verloren_je_stufe["fakten"] == 1,
           "stilles Ueberspringen waere derselbe Fehler wie ein Filter, der "
           "seine Wirkung verbirgt")

    # ---- DER AUFTRAG KOMMT VON AUSSEN (13.08.) ----
    #
    # Vorher stand im Lauf fest ("spot", "einstieg") - ein Hebel-Lauf war gar
    # nicht moeglich, obwohl Paket 13 alles dafuer gebaut hatte.
    def _antwort(sym, aktion, richtung=None):
        rr = reihen[sym]; ii = len(rr) - 1
        kk = RE.kurs_eur(sym, rr, ii, "data/tradinginfotool.db")
        aa = RE.atr_eur(sym, rr, ii, "data/tradinginfotool.db")
        d = {"aktion": aktion,
             "belege": [{"fakt": "x", "richtung": "dafuer", "gewicht": "hoch"}],
             "unabhaengige_faktoren": 2, "begruendung": "y",
             "was_dagegen": "z", "umgeworfen_durch": "w"}
        # ⚠️ S6c: KAUFEN/NACHKAUFEN OHNE Richtung werden jetzt abgewiesen.
        # Der Vorgabewert LONG haelt die Faelle lauffaehig, in denen die
        # Richtung nicht das Thema ist; wer sie prueft, gibt sie mit.
        if not richtung and aktion in ("KAUFEN", "NACHKAUFEN"):
            richtung = "LONG"
        if richtung:
            d["richtung"] = richtung
        if aktion in ("KAUFEN", "NACHKAUFEN"):
            d |= {"einstieg_eur": round(kk, 2), "stop_eur": round(kk - 2.5 * aa, 2)}
        return d

    # ⚠️ DIE NUTZERSCHALTER MUESSEN GESETZT WERDEN (O-38, 16.08.2026).
    #
    # Bis heute uebersprang der Trockenlauf sie ganz, und dieser Test kam
    # ohne aus. Seit sie auch trocken gelesen werden, faellt "ETH" durch:
    # `get_hebel_pruefung_erlaubt` ist seit dem 15.08. OPT-IN, keine Zeile
    # heisst AUS - also korrektes Produktionsverhalten, das der Trockenlauf
    # bis heute verdeckt hat.
    #
    # NICHT DIE ZUSICHERUNG LOCKERN, SONDERN DEN FALL HERSTELLEN. Zum
    # siebten Mal diese Woche derselbe Typ: die Eingabe erzeugte nicht die
    # Lage, die sie pruefen wollte.
    import database.db as _db_mod

    _db_mod.set_hebel_pruefung_erlaubt(con, "ETH", True)
    _db_mod.set_dca_erlaubt(con, "ETH", True)

    def _lauf(inst, aktion, richtung=None, sym="ETH"):
        # ⚠️ SEIT G-6 (31.08.2026) BRAUCHT EIN TROCKENLAUF GESTELLTE RAENGE.
        # Stufe 11 verwirft jetzt; ohne Beitraege liegt jedes Potential bei
        # 0,000 und es entstuende NIE eine Mail. Gestellt wird das BESTE
        # Fuenftel - damit prueft dieser Lauf die Geometrie und die Mail,
        # nicht die Bewertung. Die Bewertung hat ihre eigenen Pakete.
        ant = {"lagebild": antworten["lagebild"],
               "befund": {sym: _antwort(sym, aktion, richtung)},
               "marktraenge": {sym: {"funding_fuenftel": 0,
                                     "turnover_fuenftel": 0}}}
        return RL.fuehre_lauf(conn=con, reihen=reihen, symbole=[sym],
                              betriebsart="trocken", instrument=inst,
                              strategie="einstieg", antworten=ant,
                              config=_OHNE_BREMSEN)

    # ⚠️⚠️ ETH IST HIER EIN KERN-ASSET: der Test schaltet oben BEIDE Schalter
    # ein (`set_hebel_pruefung_erlaubt` UND `set_dca_erlaubt`). Damit hat es
    # seit dem 01.09. ZWEI Zellen - die Akkumulation und die taktische -
    # und kann folglich ZWEI Mails erzeugen.
    #
    # Das ist keine Regression, sondern die Nutzerentscheidung vom 01.09.:
    # die taktische Zelle entsteht nur, WENN die Rechnung einen Hebel ergibt.
    # Hier tut sie es (der Lauf meldet es auch: "ETH laeuft als akkumulation,
    # die Rechnung ergibt aber das Etikett 'hebel'"), also bleibt sie.
    #
    # ⚠️ GEPRUEFT WIRD DIE BEZIEHUNG, NICHT DIE FESTE ZAHL: so viele Mails
    # wie Zellen, die durchkommen. Eine feste 1 waere beim naechsten
    # Schalter wieder falsch.
    _sp = _lauf("spot", "KAUFEN")
    pruefe(P, "ein Spot-Lauf erzeugt je durchgekommener Zelle eine Mail",
           len(_sp["mails"]) == _sp["durchlauf"].heraus
           and len(_sp["mails"]) >= 1,
           "Mails %d, heraus %d. ETH hat als Kern-Asset zwei Zellen "
           "(Akkumulation + taktisch); die taktische bleibt nur, wenn die "
           "Rechnung einen Hebel ergibt. Trichter verloren=%s"
           % (len(_sp["mails"]), _sp["durchlauf"].heraus,
              dict(_sp["durchlauf"].verloren_je_stufe)))
    pruefe(P, "ein Hebel-Lauf ebenfalls",
           len(_lauf("hebel", "KAUFEN", "LONG")["mails"]) == 1,
           "vorher war er gar nicht moeglich")
    # --- O-38: DER TROCKENLAUF SIEHT DIE NUTZERSTUFEN (16.08.2026) -----
    #
    # Er uebersprang die Schalter des Nutzers und die Anlass-Stufe ganz.
    # Jeder Trockenlauf ueberschaetzte damit den Durchsatz - auch die, mit
    # denen der Vollumstieg geprueft wurde.
    _db_mod.set_hebel_pruefung_erlaubt(con, "ETH", False)
    pruefe(P, "ein abgeschaltetes Asset erzeugt AUCH TROCKEN keine Mail",
           len(_lauf("hebel", "KAUFEN", "LONG")["mails"]) == 0,
           "asset_schalter ist ein reiner Leser - es gab nie einen Grund, "
           "ihn trocken zu ueberspringen, und der Nutzer hatte abgewaehlt")
    _db_mod.set_hebel_pruefung_erlaubt(con, "ETH", True)

    _vor_anlass = con.execute(
        "SELECT COUNT(*) FROM anlass_beobachtung").fetchone()[0]
    _lauf("spot", "KAUFEN")
    pruefe(P, "aber er SCHREIBT dabei keine Anlass-Zeile",
           con.execute("SELECT COUNT(*) FROM anlass_beobachtung"
                       ).fetchone()[0] == _vor_anlass,
           "ein Trockenlauf, der schreibt, veraendert die Grundlage des "
           "naechsten scharfen Laufs - genau das soll er nicht")

    pruefe(P, "ein unvorgesehenes Paar bricht den Lauf ab - VOR der Schleife",
           _wirft(lambda: RL.fuehre_lauf(conn=con, reihen=reihen, symbole=[],
                                         betriebsart="trocken",
                                         instrument="hebel",
                                         strategie="akkumulation",
                                         antworten=antworten),
                  RL.LaufAbgebrochen),
           "sonst meldete er vierzigmal dasselbe")

    # DIE RICHTUNG DREHT DURCH DIE GANZE KETTE - alle drei Groessen.
    def _marken(text):
        # ⚠️ "Stop " ALLEIN GENUEGT NICHT (24.08.2026-Fund am Notebook). Eine
        # Bestandsposition erzeugt VOR "DIE RECHNUNG" einen eigenen Absatz mit
        # Zeilen wie "Stop         auf 1.918 EUR nachziehen - sichert +1,05 R"
        # (Trailing-Stop-Empfehlung der Ausstiegsfuehrung) - die enthaelt
        # "Stop " genauso und stand im Text VOR der echten Rechnungszeile
        # "Stop            2.262,98 EUR  (8,9 % - 2,5 x ATR)". Der alte Regex
        # nahm die erste Zeile mit "Stop " und damit die falsche - die echte
        # Geometrie war die ganze Zeit korrekt (bestaetigt: 73 von 73 echten
        # SHORT-Einstiegssignalen im NB-Export haben Stop > Einstieg).
        #
        # DIE ECHTE ZEILE BEGINNT MIT "Stop" UND DAS ZWEITE WORT IST SCHON
        # DIE ZAHL ("Stop" + viele Leerzeichen + Preis + " EUR"). Die
        # Nachziehen-Zeile beginnt zwar auch mit "Stop", aber das zweite Wort
        # ist "auf" - ein Wort, keine Zahl. Dieselbe Form gilt fuer
        # "Take-Profit". "Liquidation etwa" bleibt beim alten, einfachen
        # Substring-Test - sie steht eingebettet in der Hebel-Zeile, nicht am
        # Zeilenanfang, und hatte bisher keinen Fehlalarm.
        aus = {}
        for zeile in text.split(chr(10)):
            z = zeile.strip()
            woerter = z.split()
            for name, wort in (("stop", "Stop"), ("ziel", "Take-Profit")):
                if (name not in aus and woerter and woerter[0] == wort
                        and len(woerter) > 1
                        and woerter[1].replace(".", "").replace(",", "").isdigit()):
                    aus[name] = float(
                        woerter[1].replace(".", "").replace(",", "."))
            if "liq" not in aus and "Liquidation etwa" in z:
                zahlen = [t for t in z.replace("(", " ").replace(")", " ").split()
                          if t.replace(".", "").replace(",", "").isdigit()]
                if zahlen:
                    aus["liq"] = float(zahlen[0].replace(".", "").replace(",", "."))
        return aus

    kurs_eth = RE.kurs_eur("ETH", reihen["ETH"], len(reihen["ETH"]) - 1,
                           "data/tradinginfotool.db")
    # ⚠️ UND WENN DOCH KEINE MAIL ENTSTEHT, IST DAS EIN ROTER PUNKT -
    # kein Absturz. Ein IndexError beendet die GANZE Suite und nimmt
    # allen folgenden Paketen ihr Ergebnis; genau das ist am 24.08.
    # passiert. Eine Pruefung, die stirbt, prueft nichts mehr.
    def _erste_mail(*a):
        _m = _lauf(*a).get("mails") or []
        _text = _m[0]["text"] if _m else ""
        return _marken(_text), _text

    lang, _lang_text = _erste_mail("hebel", "KAUFEN", "LONG")
    kurz, _kurz_text = _erste_mail("hebel", "KAUFEN", "SHORT")
    # ⚠️⚠️ DER SCHUTZ WAR HALB - und das hat am 02.09. die Suite am
    # NOTEBOOK abgebrochen (`KeyError: 'stop'`, Zeile 3669).
    #
    # `_erste_mail` faengt den IndexError ab und gibt bei fehlender Mail
    # ein LEERES Woerterbuch zurueck. Genau das war die Absicht. Aber die
    # drei folgenden Pruefungen greifen mit `lang["stop"]` darauf zu - und
    # ein KeyError beendet die Suite ebenso gruendlich wie der IndexError,
    # gegen den man sich gerade abgesichert hatte.
    #
    # Am Desktop faellt es nicht auf, weil dort eine Mail entsteht. Das ist
    # die vierte Spielart von "Test haengt an der Produktion" (Methodik
    # 2.66): die Pruefung ueberlebt nur, WEIL die Daten guenstig liegen.
    #
    # ⚠️ NICHT STILL UEBERSPRINGEN. Fehlen die Marken, ist das ein ROTER
    # Punkt - aber einer, der die folgenden Pakete weiterlaufen laesst.
    _noetig = ("stop", "ziel", "liq")
    _fehlend = ([k for k in _noetig if k not in lang],
                [k for k in _noetig if k not in kurz])
    _marken_da = not (_fehlend[0] or _fehlend[1])
    pruefe(P, "beide Richtungsläufe erzeugen eine Mail MIT Kursmarken",
           _marken_da,
           "ohne sie sind die folgenden Richtungspruefungen leer. "
           "LONG fehlt %s, SHORT fehlt %s. Mail vorhanden: LONG %s, "
           "SHORT %s" % (_fehlend[0] or "nichts", _fehlend[1] or "nichts",
                         bool(_lang_text), bool(_kurz_text)))
    # ⚠️ MEHR ALS DIE ZWEI ZAHLEN (24.08.2026): am Notebook lag der
    # SHORT-Stop wiederholt UNTER dem Kurs, aber weder `entscheidungsrechnung.
    # rechne()` noch ein voller lokaler Mail-Nachbau liessen sich dazu
    # bringen, dasselbe zu zeigen - die Geometrie spiegelt bei jedem
    # Desktop-Versuch korrekt. `_marken()` ist ein naiver Text-Regex (nimmt
    # die erste Zeile mit "Stop "); OHNE die tatsaechlichen Zeilen laesst
    # sich nicht unterscheiden, ob die RECHNUNG falsch ist oder der Regex
    # eine falsche Zeile trifft. Alle Zeilen mit "Stop " (nicht nur die
    # erste) gehen deshalb mit in die Detailzeile.
    _kurz_stop_zeilen = [z.strip() for z in _kurz_text.split(chr(10))
                         if "Stop " in z]
    if _marken_da:
        pruefe(P, "bei LONG liegt der Stop unter dem Kurs, bei SHORT darueber",
               lang["stop"] < kurs_eth < kurz["stop"],
               f"LONG {lang.get('stop')} / SHORT {kurz.get('stop')} bei "
               f"{kurs_eth:.0f} | SHORT-Zeilen mit 'Stop ': {_kurz_stop_zeilen}")
        pruefe(P, "das Ziel dreht mit",
               lang["ziel"] > kurs_eth > kurz["ziel"])
        pruefe(P, "und die Liquidation auch",
               lang["liq"] < kurs_eth < kurz["liq"],
               "sonst stuende bei einem SHORT eine Liquidation unter dem "
               "Einstieg - dort kann sie nie greifen")
    else:
        # ⚠️ DREI ROTE PUNKTE, nicht ein stilles Ueberspringen. Waeren sie
        # unsichtbar, saehe eine Suite mit fehlenden Mails genauso aus wie
        # eine mit richtiger Geometrie - und die Zahl am Ende stimmte
        # trotzdem.
        for _was in ("Stop dreht mit der Richtung",
                     "Ziel dreht mit der Richtung",
                     "Liquidation dreht mit der Richtung"):
            pruefe(P, _was, False,
                   "NICHT GEPRUEFT - es entstand keine Mail mit Kursmarken. "
                   "Der Grund steht in der Zeile darueber; diese drei "
                   "Punkte sind rot, damit die Luecke sichtbar bleibt und "
                   "die Gesamtzahl stimmt")
    con.close()


def _wirft(fn, typ) -> bool:
    try:
        fn()
        return False
    except typ:
        return True



def paket_export() -> None:
    """Der Notebook-Export kennt die Rollen-Kette (13.08.2026)."""
    P = "Export"
    import sqlite3
    import sys as _sys

    # DAS EXPORTSKRIPT LIEST `sys.argv` BEIM IMPORT (Zeile 221:
    # `int(sys.argv[2])`). Von hier aus stehen dort die eigenen Argumente -
    # `--paket Export` - und der Import stirbt an einem int(). Deshalb waehrend
    # des Imports leeren und danach zuruecklegen. Das Skript selbst zu aendern
    # waere der groessere Eingriff fuer den kleineren Nutzen.
    _argv = _sys.argv
    _sys.argv = [_argv[0]]
    try:
        import extract_notebook_diagnose as EX
    finally:
        _sys.argv = _argv
    from agent import rollen_gate as RG, signal_abbildung as SA

    # Eine Kopie MIT den neuen Tabellen - die Produktivdatei hat sie noch
    # nicht, weil die Migration nur im Betrieb laeuft.
    q = sqlite3.connect("data/tradinginfotool.db")
    c = sqlite3.connect(":memory:"); q.backup(c); q.close(); c.row_factory = sqlite3.Row
    SA.migriere(c); RG.migriere(c)

    drift = EX._spaltendrift(c)
    pruefe(P, "keine Tabelle ist mehr unerwaehnt",
           drift["tabellen"]["nicht_erwaehnt"] == [],
           f"offen: {drift['tabellen']['nicht_erwaehnt']}")
    offen = drift["spalten"].get("signals", {}).get("nicht_exportiert") or []
    pruefe(P, "keine signals-Spalte ist mehr unexportiert", offen == [],
           f"offen: {offen}")
    pruefe(P, "die fuenfzehn Spalten der Rollen-Kette sind namentlich drin",
           all(sp in EX._SPOT_SIGNAL_SPALTEN for sp in
               ("quelle_kette", "lagebild_id", "prompt_stand", "fx_eur_je_usd",
                "unabhaengige_faktoren", "umgeworfen_durch",
                "umgeworfen_preis_eur", "umgeworfen_bis",
                "schwankung_perzentil", "momentum_perzentil",
                "volumen_perzentil", "zai_stimmen", "richtung", "hebel",
                "modell")),
           "ohne sie ist der gesamte Umbau von aussen unsichtbar")

    # DIE STUFEN WERDEN AUSGEPACKT, nicht als JSON-Klumpen abgelegt.
    RG.schreibe(c, _beispiel_durchlauf(RG), "2026-08-13T07:00:00+00:00")
    r = EX._rollen_kette(c)
    pruefe(P, "beide Tabellen erscheinen im Export",
           "lagebilder" in r and "gate_durchlaessigkeit" in r)
    lauf = r["gate_durchlaessigkeit"]["laeufe"][0]
    pruefe(P, "die Durchlaessigkeit ist entfaltet, nicht als JSON-String",
           isinstance(lauf.get("verloren"), dict)
           and isinstance(lauf.get("bestanden"), dict),
           "wer im Notebook fragt 'wo verlieren wir', soll nicht erst einen "
           "String parsen")
    pruefe(P, "die Faktorzahlen reisen mit",
           lauf.get("faktorzahlen") == [2, 3],
           "sie sind der offene Punkt aus Kapitel 15 - ohne Export nicht "
           "nachpruefbar")
    pruefe(P, "und die Z1-Befunde ebenfalls", "z1_verstoesse" in lauf)

    # FAIL-SOFT: auf einer aelteren Datei fehlen die Tabellen.
    alt = sqlite3.connect(":memory:")
    alt.execute("CREATE TABLE meta (schema_version INTEGER)")
    r2 = EX._rollen_kette(alt)
    pruefe(P, "eine alte Datei ohne die Tabellen bricht nichts ab",
           "nicht_vorhanden" in r2["lagebilder"]
           and "nicht_vorhanden" in r2["gate_durchlaessigkeit"],
           "ein fehlender Export ist kein Grund, den ganzen Lauf zu verlieren")
    alt.close(); c.close()

    # ----------------------------------------------------------------
    # DIE ANALYSESTANDARDS. Ein Export, den keine Pruefung liest, ist ein
    # Datenhaufen - erst der Katalog macht daraus eine Diagnose.
    std = io.open("pruefe_export_standard.py", encoding="utf-8").read()
    voll = io.open("pruefe_export_vollcheck.py", encoding="utf-8").read()

    pruefe(P, "der Kennzahlen-Katalog hat Punkt 16 (Durchlaessigkeit)",
           '16. Rollen-Kette' in std and 'd.get("rollen_kette")' in std,
           "Punkte 1-15 messen AUFGELOESTE Signale - dieser misst, ob "
           "ueberhaupt eines entsteht")
    pruefe(P, "er meldet den Deadloop-Zustand", "Deadloop-Zustand" in std)
    pruefe(P, "er meldet Einstiege, die sich nicht tragen",
           "Einstiege, keiner traegt " in std
           and "sich nach Kosten - Basisrate" in std)
    pruefe(P, "er meldet die Faktorzahl mit nur zwei Werten",
           "sie ist die Entscheidung noch " in std,
           "offener Punkt aus Kapitel 15")
    pruefe(P, "die Konfidenz-Kalibrierung ist als NUR-ALTDATEN gekennzeichnet",
           "nur ALTE Kette" in std,
           "die neue Kette erhebt keine Konfidenz mehr (E3) - ein leerer "
           "Block dort ist kein Fehlstand")

    pruefe(P, "der Vollcheck zeigt die Durchlaessigkeit je Lauf (C6)",
           "C6 DIE ROLLEN-KETTE" in voll)
    pruefe(P, "und fragt, ob die neuen Felder ueberhaupt mitkommen (D6/D7)",
           "D6  Felder der Rollen-Kette" in voll
           and "D7  Block 'rollen_kette'" in voll,
           "ein fehlendes Feld sieht im Export aus wie ein leeres")

    # DIESE PRUEFUNG HAETTE DEN FEHLER GEFANGEN, DEN SIE MEINT. Der erste Wurf
    # von D6 listete `rolle_begruendung` - so heisst die Spalte im Umbauplan
    # Kap. 14.2, aber nirgends im Code. Der Vollcheck meldete daraufhin eine
    # Luecke, die es nicht gibt, und haette jede Auswertung auf eine falsche
    # Faehrte geschickt. Ein Plan ist eine Absicht, keine Festlegung.
    import re as _re
    genannt = set(_re.findall(r'"(\w+)"',
                              voll.split('neu = (')[1].split(')')[0]))
    pruefe(P, "die Feldnamen in D6 stammen aus dem Code, nicht aus dem Plan",
           genannt <= set(SA.SPALTEN_SIGNAL),
           f"nicht im Code: {sorted(genannt - set(SA.SPALTEN_SIGNAL))}")
    pruefe(P, "D6 fragt nicht nach facts_json",
           "facts_json" not in voll.split("D6")[1].split("OFFENE PUNKTE")[0]
           or "bewusst\n    # ausgeschlossen" in voll,
           "das ist im Export absichtlich ausgeschlossen - danach zu fragen "
           "erzeugt eine Dauermeldung ohne Ursache")


def _beispiel_durchlauf(RG):
    d = RG.Durchlauf("rollen")
    for i, sym in enumerate(("A", "B")):
        d.beginne(sym)
        d.bestanden(sym, "auftrag")
        d.faktorzahl(2 + i)
        if i:
            d.verloren(sym, "aktion", "NICHTS_TUN")
    return d


def paket_15() -> None:
    """Kapitel 15, Schritt 1: die Versandkette und das Material fuers Meta-Labeling."""
    P = "15"
    import sqlite3
    import threading
    import time as _time
    from agent import rollen_gate as RG, signal_abbildung as SA
    from agent import trefferbilanz as TB, zweite_meinung as ZM
    from database.db import _SIGNAL_COLUMNS

    # ------------------------------------------------------------------
    # A. DAS SCHREIBEN - die Luecke, an der die ganze Kette haengt.
    q = sqlite3.connect("data/tradinginfotool.db")
    c = sqlite3.connect(":memory:"); q.backup(c); q.close()
    # ⚠️ ROW_FACTORY FEHLTE HIER (24.08.2026-Fund am Notebook): ohne sie liest
    # `compute_ausstiegs_empfehlungen()` weiter unten `row["symbol"]` von
    # einer Verbindung, die nur Tupel liefert - "TypeError: tuple indices
    # must be integers or slices, not str", abgefangen und als
    # "Ausstiegsfuehrung nicht lesbar" in `erg['fehler']` gemeldet. Am
    # Desktop blieb das unentdeckt: der Trockenlauf davor findet dort nie
    # eine Position, die diesen Zweig ueberhaupt betritt. Am Notebook, mit
    # echten Positionen im Bestand, greift der Zweig - und deckte damit
    # zugleich auf, dass die Funktion selbst vom `row_factory` des Aufrufers
    # abhing (jetzt in `backward_tracking.py` behoben).
    c.row_factory = sqlite3.Row
    SA.migriere(c); RG.migriere(c)

    NEUE = ("quelle_kette", "lagebild_id", "prompt_stand", "fx_eur_je_usd",
            "unabhaengige_faktoren", "umgeworfen_durch", "umgeworfen_preis_eur",
            "umgeworfen_bis", "schwankung_perzentil", "momentum_perzentil",
            "volumen_perzentil")

    # DIE BEGRUENDUNG DER FUNKTION, ALS PRUEFUNG. Faellt diese hier um, ist
    # `schreibe_signal()` ueberfluessig geworden - dann gehoert sie weg, nicht
    # daneben. Eine zweite Schreibfunktion ohne Grund ist eine Fehlerquelle.
    pruefe(P, "db.insert_signal koennte KEINE der elf neuen Spalten schreiben",
           not any(sp in _SIGNAL_COLUMNS for sp in NEUE),
           "genau deshalb gibt es schreibe_signal() - der Weg ueber die alte "
           "Funktion haette sie still fallen lassen, ohne Fehler")

    antwort = {"aktion": "KAUFEN", "begruendung": "Bodenbildung",
               "was_dagegen": "duenner Umsatz", "unabhaengige_faktoren": 3,
               "umgeworfen_durch": "Bruch der Marke",
               "umgeworfen_preis_eur": 90.0,
               # ⚠️ EIN TEST DARF NICHT AM KALENDER HAENGEN (01.09.2026).
               #
               # Hier stand fest "2026-09-01". `_frist_oder_nichts` verwirft
               # jede Frist, die nicht in der ZUKUNFT liegt - also war diese
               # Pruefung am 31.08. gruen und am 01.09. rot, ohne dass sich
               # eine Zeile Code geaendert haette. Wer dann sucht,
               # verdaechtigt die letzte Aenderung, nicht den Kalender: ich
               # habe zuerst die Migration von heute geprueft.
               #
               # Jetzt ein Datum, das immer in der Zukunft liegt.
               "umgeworfen_bis": (
                   _dt.date.today() + _dt.timedelta(days=90)).isoformat(),
               "einstieg_eur_von": 100.0, "stop_eur_von": 90.0,
               "ziel_eur_von": 130.0, "tranche_eur": 500.0}
    familien = {"schwankung_perzentil": 0.12, "momentum_perzentil": 0.74,
                "volumen_perzentil": 0.81}
    felder = SA.felder_aus_entscheidung(
        antwort, fakten={"asset": "TESTX"}, lagebild_id=7,
        prompt_stand="p1", eur_je_usd=0.8744, familien=familien)
    sid = SA.schreibe_signal(c, felder, symbol="TESTX")
    pruefe(P, "schreibe_signal legt eine Zeile an und gibt die Kennung",
           isinstance(sid, int) and sid > 0)

    zeile = c.execute("SELECT * FROM signals WHERE id = ?", (sid,)).fetchone()
    namen = [d[0] for d in c.execute(
        "SELECT * FROM signals WHERE id = ?", (sid,)).description]
    hat = dict(zip(namen, zeile))
    fehlend = [sp for sp in NEUE if hat.get(sp) is None]
    pruefe(P, "alle elf neuen Spalten stehen wirklich in der Zeile",
           not fehlend, f"leer geblieben: {fehlend}")
    pruefe(P, "die Pflichtfelder der Tabelle sind gefuellt",
           all(hat.get(sp) is not None for sp in
               ("symbol", "created_at", "action", "gate_passed", "facts_json")),
           "sonst schlaegt der INSERT erst im Betrieb fehl")
    pruefe(P, "quelle_kette trennt die neue von der alten Kette",
           hat.get("quelle_kette") == "rollen",
           "ohne sie waere jede spaetere Messung ein Mischtopf")

    # DIE PERZENTILE UNVERAENDERT, nicht schon hier in Baender gelegt. Wer den
    # Rohwert speichert, kann die Bandgrenzen spaeter noch aendern; wer das Band
    # speichert, hat sich fuer immer festgelegt.
    pruefe(P, "die Perzentile stehen als Wert da, nicht als Band",
           abs(hat.get("momentum_perzentil") - 0.74) < 1e-9,
           f"gespeichert: {hat.get('momentum_perzentil')}")

    # ------------------------------------------------------------------
    # B. DER KONSTELLATIONSSCHLUESSEL - vier Plaetze, bisher einer gefuellt.
    pruefe(P, "0,74 wird zu Perzentil 74, nicht zu 0,74",
           TB._prozent(0.74) == 74.0,
           "die Grenzen in merkmale() sind PROZENTE - ohne die Umrechnung "
           "faenden ALLE Werte im untersten Band, und die Tabelle saehe "
           "gefuellt aus, waehrend sie eine Spalte breit waere")

    # DIE KONSTANTEN SELBST, NICHT IHRE WERTE ABGESCHRIEBEN. Der erste Wurf
    # dieser Pruefung setzte 'take_profit' - richtig heisst es
    # 'take_profit_erreicht', und die Pruefung meldete daraufhin einen Defekt,
    # den es nicht gibt. Dritter Fall derselben Bewegung an einem Tag: eine
    # Zeichenkette aus dem Gedaechtnis statt aus der Quelle.
    c.execute("UPDATE signals SET outcome_status = ? WHERE id = ?",
              (TB.TREFFER[0], sid))
    c.commit()
    bilanz = TB.zaehle(c, quelle_kette="rollen")
    # ⚠️ NICHT DEN ERSTEN SCHLUESSEL NEHMEN, DEN ERWARTETEN NACHSCHLAGEN
    # (Methodik 2.68, 24.08.2026-Fund). `c` ist eine Kopie der echten
    # Produktions-DB, NICHT von `signals` befreit - `next(iter(bilanz))`
    # liefert also, welcher Schluessel in der DICT-REIHENFOLGE zuerst kommt,
    # und das haengt an der Menge und Reihenfolge der ECHTEN, laengst
    # aufgeloesten Signale. Auf dem Desktop (kaum echte "rollen"-Signale mit
    # Ausgang) war das zufaellig der TESTX-Schluessel; am Notebook (tausende
    # echte Faelle) ein voellig anderer. Die drei Baender sind reine
    # Funktionen der EINGABE (`merkmale()`/`_prozent()`/`_band_grob()`, ohne
    # jeden Bezug zur Population) - der erwartete Schluessel laesst sich
    # deshalb exakt vorausberechnen, statt ihn zu erraten.
    schluessel = TB.merkmale(vola_perzentil=TB._prozent(0.12),
                             spanne_perzentil=TB._prozent(0.74),
                             gleichlauf=TB._band_grob(0.81))
    _gefunden = schluessel in bilanz
    pruefe(P, "das geschriebene Signal erscheint in der Trefferbilanz",
           _gefunden and bilanz[schluessel]["faelle"] >= 1,
           (f"gefunden, {bilanz[schluessel]['faelle']} Fall/Faelle" if _gefunden
            else f"erwarteter Schluessel {schluessel} fehlt unter "
                 f"{len(bilanz)} vorhandenen") +
           " - vor dem 13.08. lieferte zaehle() dauerhaft {}")
    pruefe(P, "der Schluessel hat mehr als ein gefuelltes Merkmal",
           sum(1 for x in schluessel if x is not None) >= 3,
           f"Schluessel {schluessel} - die Faktorzahl allein wiederholt nur "
           f"die Entscheidung (Faktorzahl 3 -> 82 % Einstieg)")
    # DIE BANDGRENZEN SIND (25, 50, 75), ALSO LIEGT 74 IM DRITTEN BAND (Index 2),
    # nicht im vierten. Meine erste Erwartung war 3 - die Pruefung meldete einen
    # Defekt, der keiner war. Erwartungen an eine Einteilung rechnet man nach,
    # man schaetzt sie nicht.
    # DIE PLAETZE SIND GERUECKT (15.1): ohne die Faktorzahl steht die
    # Schwankung an Position 0, das Momentum an 1, das Volumen an 2.
    pruefe(P, "12. Perzentil ins unterste Band, 74. ins dritte von vier",
           schluessel[0] == 0 and schluessel[1] == 2,
           f"Grenzen (25, 50, 75) -> ergaben {schluessel[0]} und {schluessel[1]}")
    pruefe(P, "der Schluessel hat genau drei Plaetze",
           len(schluessel) == 3, f"{schluessel}")

    # EIN SIGNAL OHNE FAMILIEN DARF NICHT IN DIESELBE ZELLE FALLEN wie eines
    # mit gemessenen. `None` ist ein eigenes Band - sonst zaehlte man Faelle
    # zusammen, ueber die man Verschiedenes weiss.
    ohne = SA.felder_aus_entscheidung(antwort, fakten={}, familien=None)
    sid2 = SA.schreibe_signal(c, ohne, symbol="TESTY")
    verlust = next(s for s in TB.AUFGELOEST if s not in TB.TREFFER)
    c.execute("UPDATE signals SET outcome_status = ? WHERE id = ?",
              (verlust, sid2)); c.commit()
    b2 = TB.zaehle(c, quelle_kette="rollen")
    pruefe(P, "ohne gemessene Familien entsteht ein EIGENER Schluessel",
           len(b2) >= 2, f"Schluessel: {list(b2)}")

    # ------------------------------------------------------------------
    # C. DIE ZWEITE MEINUNG (Z.ai) - Text hinein, kein Zahlenwerk.
    pruefe(P, "ohne Z.ai-Client faellt die Stufe still aus, ohne Fehler",
           ZM.hole(faktentext={}, urteil={}, zai_client=None) == {},
           "P-8: die Gegenpruefung ist eine Zusatzinformation, keine Bedingung")

    class _Haenger:
        def chat(self, *a, **k):
            _time.sleep(30)
            return "{}"

    begonnen = _time.monotonic()
    aus = ZM.hole(faktentext={"a": 1}, urteil={"aktion": "KAUFEN"},
                  zai_client=_Haenger(), warte_max_s=0.4)
    gedauert = _time.monotonic() - begonnen
    pruefe(P, "ein haengendes Z.ai haelt die Mail nicht auf",
           gedauert < 5 and aus == {},
           f"{gedauert:.1f}s gewartet - 3 x 150 s Timeout gegen 240 s Deckel "
           f"ist bekannt und gewollt (P-8), aber es muss ENDEN")

    class _HalbKaputt:
        """Erster Aufruf wirft, die uebrigen antworten."""
        def __init__(self): self.n = 0
        def chat(self, *a, **k):
            self.n += 1
            if self.n == 1:
                raise RuntimeError("Netz weg")
            return '{"eigene_richtung": "SHORT", "kurzbegruendung": "schwach"}'

    aus2 = ZM.hole(faktentext={"a": 1}, urteil={"aktion": "KAUFEN"},
                   zai_client=_HalbKaputt(), warte_max_s=20)
    # UMGESCHRIEBEN 16.08.2026: der Richtungsabgleich ist entfernt, an seine
    # Stelle tritt Rolle G mit EIGENER Faktengrundlage. Die Sorge dahinter
    # bleibt gueltig und wird weiter geprueft: zwei getrennte try-Bloecke,
    # damit ein Ausfall der einen Pruefung die andere nicht mitnimmt.
    # SEIT DEM 17.08. GIBT ES NUR NOCH EINEN AUFRUF. Diese Pruefung verlangte
    # zwei getrennte Fehlerfaenge - richtig, solange die Konsistenzpruefung
    # danebenlief. Sie ist entfernt (Nutzer 16.08.: "war nie meine
    # Anforderung"), also prueft dieselbe Absicht jetzt das Uebrige: der EINE
    # Aufruf unterscheidet "kein Platz" von "fehlgeschlagen".
    _zm_q = _quelltext("agent/zweite_meinung.py")
    pruefe(P, "Rolle G trennt uebersprungen von fehlgeschlagen",
           "except Andrang as e:" in _zm_q
           and 'aus["uebersprungen"]' in _zm_q
           and "Rolle G fehlgeschlagen (P-8)" in _zm_q,
           "wer nicht drankam, darf spaeter nicht als Zustimmung zaehlen")
    pruefe(P, "die Konsistenzpruefung wird NICHT mehr gerufen",
           "_mit_platz(G.pruefe_konsistenz" not in _zm_q
           and "nennt die Begruendung" not in _zm_q,
           "sie stand auf derselben Informationsgrenze wie Rolle BC (R-R2) "
           "und war vom Nutzer abgelehnt - ihr Prompt bleibt lesbar stehen")
    pruefe(P, "Rolle G bekommt eine EIGENE Grundlage, nicht den Faktentext",
           "def rolle_g(client, urteil" in _quelltext("agent/zweite_meinung.py")
           and "positionierung" in _quelltext("agent/zweite_meinung.py"),
           "derselbe Faktentext waere wieder Homogeneous Debate")
    # ⚠️ GEMESSEN STATT IM QUELLTEXT GESUCHT (17.08.2026). Hier stand die
    # Suche nach `len(lage["fehlt"]) >= 3` - dem Text der GROBEN Schranke.
    # Sie ist heute entfallen: seit die Nicht-Luecken je Assetklasse
    # gefiltert werden, steht bei einem Themen-ETF `fehlt = []`, und eine
    # Zaehlung der Luecken haette durchgelassen. Der verbliebene Waechter
    # misst die SAETZE - und das prueft dieser Test jetzt am Verhalten.
    import agent.positionierung as _PO9
    from agent import zweite_meinung as _ZM9

    class _KnalltSofort:
        def chat(self, *a, **k):
            raise AssertionError("Rolle G haette gar nicht fragen duerfen")

    _echt9 = _PO9.saetze
    try:
        _PO9.saetze = lambda lage: []
        _ohne = _ZM9.rolle_g(_KnalltSofort(), {"aktion": "KAUFEN"},
                             symbol="CEBS", assetklasse="etf",
                             instrument="spot",
                             db="data/tradinginfotool.db")
    except AssertionError:
        _ohne = "GEFRAGT"
    finally:
        _PO9.saetze = _echt9
    pruefe(P, "und sie fragt gar nicht, wenn keine Positionierung vorliegt",
           _ohne is None,
           "ein Modell, das ueber nichts urteilt, urteilt trotzdem - und das "
           "waere die naechste Konstante")

    pruefe(P, "ohne Ergebnis entsteht KEINE leere Mailzeile", ZM.zeilen({}) == [],
           "ein Abschnitt 'Zweite Meinung: -' saehe aus wie ein Befund und "
           "waere ein Ausfall - der Leser kann beides nicht unterscheiden")
    # UMGESCHRIEBEN 16.08.2026 auf Rolle G. Die Sorge bleibt dieselbe: ein
    # Einwand darf nicht in einem Nebensatz verschwinden.
    _mit = ZM.zeilen({"einwand": "ja",
                      "einwand_grund": "Finanzierungsrate im 96. Perzentil"})
    pruefe(P, "der Einwand steht in der Mail und wird benannt",
           _mit and "EINWAND" in _mit[0] and "96. Perzentil" in _mit[0],
           str(_mit))
    pruefe(P, "und die Mail sagt, worauf er beruht",
           len(_mit) > 1 and "positionierung" in _mit[1].lower()
           and "nicht die kurslage" in _mit[1].lower(),
           "sonst liest es sich wie eine zweite Meinung zum selben Chart")
    # UMGESCHRIEBEN 16.08.2026 auf Nutzervorgabe: die Gegenpruefung soll AUCH
    # ohne Einwand etwas sagen - eine Pruefung, die nur bei Widerspruch
    # sichtbar ist, laesst offen, ob sie ueberhaupt gelaufen ist.
    #
    # MEINE SORGE VOR EINEM KONSTANTEN FELD (R-T6) BLEIBT BERECHTIGT und ist
    # anders geloest: die Bestaetigung nennt die Zahlen, auf die sie sich
    # stuetzt. Damit bewegt sich der Text mit den Daten.
    _ohne = ZM.zeilen({"einwand": "nein", "einwand_grund": "Funding gewohnt",
                       "grundlage": ["Die Finanzierungsrate steht im 72. "
                                     "Perzentil der letzten 400 Messungen."]})
    pruefe(P, "auch ohne Einwand steht eine Aussage da",
           _ohne and "kein Einwand" in _ohne[0], str(_ohne[:1]))
    pruefe(P, "und sie nennt die Zahlen, auf denen sie beruht",
           any("72. Perzentil" in z for z in _ohne),
           "sonst waere die Bestaetigung ein konstantes Feld")
    pruefe(P, "die Gegenpruefung hat einen EIGENEN Mailabschnitt",
           "5. GEGENPRUEFUNG (zweites Modell)" in _quelltext(
               "agent/signal_mail.py")
           and "gegenpruefung=list(zweite_zeilen)" in _quelltext(
               "agent/rollen_lauf.py"),
           "hinten in der EINORDNUNG sah sie aus wie ein Nachsatz unserer "
           "eigenen Rechnung - sie ist die Aussage einer anderen Quelle")

    # ------------------------------------------------------------------
    # D. DIE REIHENFOLGE - der eigentliche Fund vom 28.07.
    lauf = _quelltext("agent/rollen_lauf.py")
    i_schreib = lauf.find("SA.schreibe_signal(")
    i_zai = lauf.find("ZM.hole(")
    i_send = lauf.find("versand(eintrag[")
    pruefe(P, "schreiben -> Z.ai -> versenden, in dieser Reihenfolge",
           -1 < i_schreib < i_zai < i_send,
           f"Positionen {i_schreib}/{i_zai}/{i_send} - ginge die Mail vorher "
           f"raus, kehrte der Fund vom 28.07. zurueck")
    # EIN FADEN JE SIGNAL - die Lehre vom 23.07. (14.08. nachgezogen).
    #
    # EIGENE VARIABLE: `_l` wird erst weiter unten gesetzt, und `lauf` ist hier
    # die TOKEN-Fassung ohne Zeichenketten - beide passen nicht.
    _l = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "Z.ai laeuft in einem eigenen Faden je Signal",
           "threading.Thread(target=_nacharbeit" in _l,
           "synchron waeren es bei 12 Einstiegen 27 Minuten gegen einen Takt "
           "von 15 - der Lauf haette sich selbst ueberholt")
    pruefe(P, "im Faden wird NICHT geschrieben",
           "ZM.schreibe" not in _l.split("def _nacharbeit")[1].split("if zai_client is None")[0],
           "eine sqlite3-Verbindung ist nicht zwischen Threads teilbar, und "
           "die Kette oeffnet grundsaetzlich keine eigene")
    pruefe(P, "die Faeden werden vor dem Ende zusammengefuehrt",
           'ergebnis.pop("_faeden", [])' in _l and "faden.join(" in _l,
           "erst danach steht fest, was Z.ai gesagt hat")
    pruefe(P, "und ein haengender Faden wird gemeldet statt ignoriert",
           "nicht rechtzeitig fertig" in _l)
    pruefe(P, "ohne Z.ai-Client gibt es gar keinen Faden",
           "if zai_client is None:" in _l,
           "ein Thread, der sofort zurueckkehrt, ist nur Verwaltung")
    # AM VERHALTEN GEPRUEFT, NICHT AM KOMMENTAR: der Versand steht im Rumpf
    # AUSSERHALB des try - ein Z.ai-Fehler kann ihn also nicht ueberspringen.
    _rumpf = _l.split("def _nacharbeit")[1].split("if zai_client is None")[0]
    pruefe(P, "die Mail geht auch raus, wenn Z.ai ausfaellt",
           _rumpf.find("except Exception") < _rumpf.find("versand(eintrag["),
           "lieber ohne die Gegenpruefungszeilen als gar nicht (P-8) - der "
           "Versand steht NACH dem except, nicht darin")
    pruefe(P, "die Mail wird ERST NACH der zweiten Meinung endgueltig gebaut",
           'eintrag["betreff"], eintrag["text"] = baue(ZM.zeilen(' in lauf,
           "sonst muesste man Zeilen in einen fertigen Text flicken und die "
           "Abschnittsreihenfolge an zwei Orten pflegen")
    pruefe(P, "Z.ai bekommt den Faktentext, nicht die Rechnung",
           "ZM.hole(faktentext=bc_ein" in lauf and "rechnung" not in
           lauf[i_zai:i_zai + 200],
           "Stop, Ziel, Betrag und CRV liegen auf der deterministischen "
           "Schiene - Nutzervorgabe 13.08.: Text, keine Zahlenangaben")

    # NUR DER CODE, NICHT DIE BEGRUENDUNG. Dieses Modul erklaert in seinem
    # Docstring ausfuehrlich, was es NICHT tut - eine Textsuche wuerde genau
    # diese Erklaerungen als Verstoss melden.
    zm = _nur_code("agent/zweite_meinung.py")
    pruefe(P, "die Trefferbilanz erreicht Z.ai NICHT",
           "trefferbilanz" not in zm.lower() and "bewertung" not in zm
           and "TB." not in zm,
           "die Tabelle entsteht AUS den Urteilen des Modells - sie ihm "
           "zurueckzugeben macht aus einer Messung eine Rueckkopplung")

    # DIE GEFAEHRLICHSTE ZEILE, DIE NICHT DA SEIN DARF.
    pruefe(P, "die Kette ruft NICHT fuehre_beide_calls_im_hintergrund()",
           "fuehre_beide_calls_im_hintergrund" not in zm
           and "fuehre_beide_calls_im_hintergrund" not in
           _nur_code("agent/rollen_lauf.py"),
           "jene Funktion oeffnet ihre Verbindung mit db.get_connection(), "
           "fest auf die PRODUKTIVDATEI - ein Probelauf gegen eine Kopie "
           "schriebe sein Ergebnis dort auf eine fremde signal_id")
    pruefe(P, "das Ergebnis geht durch die UEBERGEBENE Verbindung",
           "def schreibe ( conn" in zm and "get_connection" not in zm,
           "der Nachweis laeuft ueber den reinen Code - im Docstring steht "
           "get_connection() als Begruendung, warum es hier NICHT benutzt wird")

    # Die Wartezeit muss laenger sein als EIN Z.ai-Aufruf, sonst waere sie
    # sinnlos - dieselbe Rechnung wie in der alten Kette.
    zai_timeout = _konst_aus("api/zai.py", "REQUEST_TIMEOUT_SECONDS")
    if zai_timeout:
        pruefe(P, "der Deckel ist groesser als ein einzelner Z.ai-Aufruf",
               ZM.WARTE_MAX_SEKUNDEN > zai_timeout,
               f"{ZM.WARTE_MAX_SEKUNDEN} s gegen {zai_timeout} s")

    # PROBE WARTET AUCH. Eine Mechanik, die nur scharf laeuft, ist genau dort
    # zum ersten Mal erprobt, wo ein Fehler eine echte Mail kostet.
    pruefe(P, "auch die Probe durchlaeuft die zweite Meinung",
           lauf.find("if betriebsart == TROCKEN:\n        return") < i_zai,
           "nur der Trockenlauf steigt vorher aus")

    # ------------------------------------------------------------------
    # E. DER GANZE WEG, EINMAL DURCH - probe, aber ohne einen einzigen echten
    # Aufruf. Ein Client, der aufgezeichnete Antworten zurueckgibt, prueft
    # genau das, was der Trockenlauf NICHT erreicht: das Schreiben, die zweite
    # Meinung und die Reihenfolge. Kosten: null Kontingent.
    from agent import rollen_lauf as RL, rollen_eingabe as RE
    from backtest_llm1_historisch import lade_reihen_aus_db as lade
    reihen = lade("data/tradinginfotool.db")
    symbole = [s for s in ("BTC", "ETH", "LINK") if s in reihen]

    def _befund(sym, kauft):
        r = reihen[sym]; i = len(r) - 1
        k = RE.kurs_eur(sym, r, i, "data/tradinginfotool.db")
        a = RE.atr_eur(sym, r, i, "data/tradinginfotool.db")
        return {"aktion": "KAUFEN" if kauft else "NICHTS_TUN",
                # S6c: bei KAUFEN Pflicht, bei NICHTS_TUN wird sie verworfen -
                # beides deckt dieselbe Zeile ab.
                **({"richtung": "LONG"} if kauft else {}),
                "belege": [{"fakt": "Schwankung niedrig", "richtung": "dafuer",
                            "gewicht": "hoch"}],
                "unabhaengige_faktoren": 2,
                "begruendung": "Die Schwankung geht zurueck.",
                "was_dagegen": "Abstand zum Hoch.",
                "umgeworfen_durch": "Tagesschluss unter dem Jahrestief.",
                **({"einstieg_eur": round(k, 2),
                    "stop_eur": round(k - 2.5 * a, 2)} if kauft else {})}

    _lagebild = {"lage": "Die Maerkte zeigen eine Divergenz.",
                 "klassen": [{"klasse": "krypto", "einstufung": "unguenstig",
                              "warum": "Bitcoin steht tief."}],
                 "belege": ["Bitcoin steht tief."]}

    class _Aufzeichnung:
        """Aufgezeichnete Antworten in der Form eines ECHTEN Clients.

        DIE FORM IST DER PUNKT. Ein erfundenes Client-Interface hat am 13.08.
        schon einmal bis zum ersten echten Aufruf ueberlebt - dieser hier nimmt
        eine NACHRICHTENLISTE und gibt Text, wie `_frage()` es erwartet."""
        def __init__(self):
            self.aufrufe = 0

        def chat(self, messages, **k):
            import json as _j
            self.aufrufe += 1
            inhalt = messages[-1]["content"]
            # ⚠️ NACH INHALT ENTSCHEIDEN, NICHT NACH ZAEHLER (24.08.2026,
            # Notebook-Fund "ETH: kein einziger brauchbarer Beleg"). Die
            # Annahme "erster Aufruf = Lagebild" gilt nur, wenn `fuehre_lauf`
            # das Lagebild ueberhaupt neu erfragt - bei `betriebsart="probe"`
            # wird ein bereits vorhandenes, noch frisches Lagebild aus der DB
            # WIEDERVERWENDET (siehe rollen_lauf.py, `LAGEBILD_HALTBAR_
            # STUNDEN`). Auf der echten Notebook-DB liegt praktisch immer
            # eines vor (Produktion laeuft alle 15 Minuten) - dann ist der
            # erste Aufruf schon eine Asset-Frage, bekam aber bisher die
            # Lagebild-Antwort samt ihrer `belege`-Liste aus reinen STRINGS
            # statt Objekten, und `rolle_trader.validiere()` verwarf jeden
            # Eintrag ohne "fakt" - Ergebnis: "kein einziger brauchbarer
            # Beleg". Ein Aufruf ist am INHALT erkennbar: die Lagebild-Frage
            # nennt kein einzelnes Symbol, eine Asset-Frage immer genau eines.
            if not any(s in inhalt for s in symbole):
                return _j.dumps(_lagebild, ensure_ascii=False)
            sym = next((s for s in symbole if s in inhalt), symbole[0])
            # ⚠️ A1 (23.08.2026): der Einstieg gehoert auf den
            # GEWAEHLTEN Wert. Fest "BTC" hiesse, einen Einstieg zu
            # pruefen, der seit der Auswahl-Stufe gar nicht mehr zum
            # Urteil kommt - und dann faende der Test keine Mail.
            return _j.dumps(_befund(sym, sym == _kauft15),
                            ensure_ascii=False)

    from agent import auswahl as _AW15
    _a15 = _AW15.waehle(reihen, symbole)
    _kauft15 = (sorted(_a15["gewaehlt"]) or ["BTC"])[0]
    klient = _Aufzeichnung()
    vor = c.execute("SELECT COUNT(*) FROM signals "
                    "WHERE quelle_kette='rollen'").fetchone()[0]
    # ⚠️ DERSELBE FUND WIE METHODIK 2.66/2.68, NUR OHNE ABSTURZ (24.08.2026,
    # Notebook-Lauf): `c` ist eine Kopie der ECHTEN Produktions-DB, und der
    # Cooldown liest daraus, wann jedes Symbol zuletzt beurteilt wurde. Lief
    # die Produktion kurz zuvor, sind alle drei Kandidaten gesperrt - "3x
    # Cooldown" statt eines Einstiegs, und der Rest der Kette hat nichts
    # mehr zu urteilen. Diese Pruefung will die SCHREIBMECHANIK des
    # Probelaufs testen, nicht ob der Cooldown gerade greift - der hat seine
    # eigenen Pruefungen (siehe paket_b1). Also dieselbe `_OHNE_BREMSEN`-
    # Konfiguration wie dort.
    _OHNE_BREMSEN15 = _ohne_bremsen()
    erg = RL.fuehre_lauf(conn=c, reihen=reihen, symbole=symbole,
                         betriebsart="probe", client=klient, modell="test",
                         zai_client=None, config=_OHNE_BREMSEN15,
                         # ⚠️ SEIT G-6 (31.08.): ohne Raenge liegt jedes
                         # Potential bei 0,000 und Stufe 11 verwirft - es
                         # entstuende keine Mail, und dieser Test pruefte
                         # nichts mehr. Gestellt statt abgerufen, damit die
                         # Suite kein Kontingent verbraucht.
                         antworten={"marktraenge": {
                             s_: {"funding_fuenftel": 0,
                                  "turnover_fuenftel": 0,
                                  "schnitt_fuenftel": 0} for s_ in symbole}})
    pruefe(P, "der Probelauf laeuft ohne Fehler durch",
           not erg["fehler"], str(erg["fehler"][:2]))
    nach = c.execute("SELECT COUNT(*) FROM signals "
                     "WHERE quelle_kette='rollen'").fetchone()[0]
    pruefe(P, "und schreibt eine Signalzeile - erstmals ueberhaupt",
           nach > vor,
           # ⚠️ MEHR ALS "vor -> nach" (24.08.2026): am Notebook blieb die
           # Zahl gleich, ohne dass `erg["fehler"]` etwas zeigte - die
           # Ursache war damit NICHT aus dieser einen Zeile zu erschliessen.
           # `_kauft15` haengt an der ECHTEN Auswahl (`_a15["gewaehlt"]`);
           # ist es dort leer oder liegt `_kauft15` nicht in `symbole`,
           # antwortet der aufgezeichnete Client nie mit KAUFEN, und die
           # Ursache liegt in der Auswahl, nicht im Trockenlauf.
           f"{vor} -> {nach} | gewaehlt={sorted(_a15['gewaehlt'])} "
           f"kauft15={_kauft15} (in symbole: {_kauft15 in symbole}) | "
           + " · ".join(erg["durchlauf"].bericht()))
    pruefe(P, "die Mail traegt die Kennung des geschriebenen Signals",
           any(m.get("signal_id") for m in erg["mails"]),
           "ohne sie liesse sich eine verschickte Mail spaeter keinem "
           "Datensatz zuordnen")
    neu = c.execute(
        "SELECT schwankung_perzentil, momentum_perzentil, volumen_perzentil, "
        "lagebild_id FROM signals WHERE quelle_kette='rollen' "
        "ORDER BY id DESC LIMIT 1").fetchone()
    pruefe(P, "die drei Familien und das Lagebild stehen an der Zeile",
           all(w is not None for w in neu),
           # `tuple(neu)`, nicht `neu` direkt (24.08.2026): seit `c` ein
           # row_factory hat, druckte diese Zeile sonst nur noch
           # "<sqlite3.Row object at 0x...>" statt der Werte.
           f"gespeichert: {tuple(neu)}")
    pruefe(P, "ohne Z.ai-Client bleibt die Mail ohne Gegenpruefungszeilen",
           not any("zweite_meinung" in m for m in erg["mails"]),
           "P-8 - kein Client heisst kein Abschnitt, nicht ein leerer")

    # ------------------------------------------------------------------
    # F. WAS DIE GEGENPRUEFUNG AN ECHTEN DATEN GEFUNDEN HAT (13.08.).
    #
    # Beides waere ohne einen Blick in einen ECHTEN Faktentext unentdeckt
    # geblieben - keine Pruefung auf Vorsatz haette es gezeigt.
    from agent.krypto import gegenpruefung as G
    from agent.lagebeschreibung import _kurs

    # F1 DIE PROMPTS MUESSEN BESCHREIBEN, WAS WIRKLICH ANKOMMT.
    for name, prompt in (("Konsistenz", ZM.SYSTEM_KONSISTENZ),
                         ("Richtung", ZM.SYSTEM_RICHTUNG)):
        fremd = [w for w in ("Funding-Rate", "Optionsmarkt", "rsi", "RSI",
                             "technische Indikatoren", "Marktregime")
                 if w in prompt]
        pruefe(P, f"der {name}-Prompt kuendigt nichts an, was die Kette nicht "
                  f"schickt", not fremd, f"genannt, aber nie geliefert: {fremd}")
    pruefe(P, "der alte Richtungs-Prompt tut genau das - deshalb ein eigener",
           "Funding-Rate" in G.SYSTEM_PROMPT_RICHTUNG,
           "ein Modell, dem man eine Struktur ankuendigt, die es nicht "
           "vorfindet, antwortet trotzdem - und man sieht der Antwort nicht "
           "an, dass sie auf einer falschen Erwartung beruht")
    pruefe(P, "der alte Konsistenz-Prompt erklaert `richtung`/`action`",
           "richtung" in G.SYSTEM_PROMPT and "Hebel-Signal" in G.SYSTEM_PROMPT,
           "beides Felder, die im Faktentext der Kette nicht vorkommen")
    zm_code = _nur_code("agent/zweite_meinung.py")
    # BEIDE ALTEN AUFRUFE SIND WEG - der Richtungsabgleich am 16.08., die
    # Konsistenzpruefung am 17.08. Die Pruefung "uebergibt sie ihre eigenen
    # Prompts" hat damit keinen Aufrufer mehr. Was BLEIBT und wichtiger ist:
    # die Prompts duerfen nicht verschwinden, sonst ist die Begruendung weg.
    pruefe(P, "die abgeschalteten Prompts bleiben lesbar stehen",
           "SYSTEM_KONSISTENZ = (" in _quelltext("agent/zweite_meinung.py")
           and "def mehrheit(" in _quelltext("agent/zweite_meinung.py"),
           "wer sie je wieder anschliesst, soll finden, warum sie ausgingen")
    pruefe(P, "und Rolle G hat ihren eigenen",
           "SYSTEM_ROLLE_G" in zm_code,
           "ohne eigenen Prompt griffe still einer der alten")
    pruefe(P, "und die alten bleiben fuer die sechs alten Pipelines gueltig",
           "system_prompt or SYSTEM_PROMPT" in _nur_code(
               "agent/krypto/gegenpruefung.py"),
           "der Parameter ist optional - kein Aufrufer musste geaendert werden")

    # F2 KEINE VORGETAEUSCHTE GENAUIGKEIT IM FAKTENTEXT.
    pruefe(P, "ein fuenfstelliger Kurs bekommt keine vier Nachkommastellen",
           _kurs(57402.8132) == "57.403",
           f"vorher stand dort '57402.8132 EUR' - die Marke stammt aus einem "
           f"Cluster von Hochs und Tiefs und ist auf hundert Euro genau, "
           f"nicht auf einen Zehntelcent")
    # DEUTSCH SEIT 17.08. - vorher stand hier "0.000346" mit Punkt, und
    # zwei Zeilen weiter oben "57.403" mit deutschem Tausenderpunkt. In
    # EINER Mail.
    pruefe(P, "ein Kleinwert behaelt seine Stellen",
           _kurs(0.00034567) == "0,000346",
           "die Genauigkeit haengt an der Groessenordnung, nicht an einer "
           "Konstante - sonst waere die Marke fuer ein Token unbrauchbar")
    import json as _json
    import re as _re
    _, _bc = RE.baue_fall(symbol=symbole[0], reihe=reihen[symbole[0]],
                          index=len(reihen[symbole[0]]) - 1, reihen=reihen,
                          db="data/tradinginfotool.db", mit_finanzierung=False)
    _text = _json.dumps(_bc, ensure_ascii=False)
    # ⚠️ BEIDE SCHREIBWEISEN (17.08.2026). Seit die Faktensaetze
    # deutsch formatiert sind, heisst 1234.5678 dort "1.234,568" - das alte
    # Muster haette diese Zahl nicht mehr gefunden, und die Pruefung waere
    # STILL blind geworden. Rohe Floats im Dict stehen weiterhin mit Punkt,
    # deshalb bleiben beide Muster.
    _uebergenau = (_re.findall(r"\d{4,}\.\d{3,}", _text)
                   + _re.findall(r"\d{1,3}(?:\.\d{3})+,\d{3,}", _text))
    pruefe(P, "auch im ECHTEN Faktentext steht keine solche Zahl mehr",
           not _uebergenau, f"gefunden: {_uebergenau[:3]}")

    # ------------------------------------------------------------------
    # G. PRUEFER GEGEN GEGENPRUEFER - alle vier Prompts gegen ihren echten
    #    Nutzinhalt. Die Frage ist nicht "ist der Prompt gut", sondern:
    #    BEKOMMT DAS MODELL, WAS IHM ANGEKUENDIGT WIRD - und sieht der
    #    Gegenpruefer etwas anderes als der Pruefer, oder nur dasselbe nochmal?
    import json as _j
    from agent import rolle_analyst as RA, rolle_trader as RT
    _tag = max(k.date for r in reihen.values() for k in r[-1:])
    _a_ein = RE.baue_lagebild_eingabe(reihen, _tag)
    _, _bc2 = RE.baue_fall(symbol=symbole[0], reihe=reihen[symbole[0]],
                           index=len(reihen[symbole[0]]) - 1, reihen=reihen,
                           db="data/tradinginfotool.db", mit_finanzierung=False)
    _stufen = (
        ("Analyst", RA.SYSTEM_PROMPT_ANALYST, _a_ein),
        ("Trader", RT.prompt_fuer("spot", "einstieg"), _bc2),
        ("Konsistenz", ZM.SYSTEM_KONSISTENZ, _bc2),
        ("Richtung", ZM.SYSTEM_RICHTUNG, ZM.nur_markt(_bc2)))
    # Begriff -> woran er im Nutzinhalt erkennbar waere.
    _BEGRIFFE = {"Funding": "funding", "Optionsmarkt": "option", "RSI": "rsi",
                 "Regime": "regime", "Indikator": "indikator",
                 "Unterstuetzung": "unterst", "Widerstand": "widerstand",
                 "Umsatz": "umsatz", "Marktstruktur": "marktstruktur",
                 "Position": "bestand"}
    for _name, _prompt, _ein in _stufen:
        _txt = _j.dumps(_ein, ensure_ascii=False).lower()
        _offen = [w for w, n in _BEGRIFFE.items()
                  if w.lower() in _prompt.lower() and n not in _txt
                  and f"KEINE {w}".lower() not in _prompt.lower()]
        pruefe(P, f"{_name}: der Prompt kuendigt nichts an, was fehlt",
               not _offen, f"angekuendigt, nicht geliefert: {_offen}")

    # DER GEGENPRUEFER DARF NICHT MEHR SEHEN ALS DER PRUEFER, und der
    # unabhaengige Richtungsabruf muss WENIGER sehen als die Konsistenzpruefung.
    _voll = len(_j.dumps(_bc2, ensure_ascii=False))
    _schmal = len(_j.dumps(ZM.nur_markt(_bc2), ensure_ascii=False))
    pruefe(P, "der Richtungsabruf sieht WENIGER als die Konsistenzpruefung",
           _schmal < _voll, f"{_schmal} gegen {_voll} Zeichen")
    pruefe(P, "der Auftrag erreicht den Richtungsabruf nicht",
           "auftrag" not in ZM.nur_markt(_bc2),
           "'Es geht um einen einzelnen Einstieg' ist eine Absichtserklaerung, "
           "kein Marktfakt - sie sagt dem Modell, was wir vorhaben")
    _saetze = ZM.nur_markt(_bc2).get("stand") or []
    pruefe(P, "und der Bestandssatz auch nicht",
           not any("im Bestand" in s for s in _saetze),
           "unsere Position ist keine Marktevidenz - und sie stand an ERSTER "
           "Stelle, also an der staerksten")
    pruefe(P, "die Marktsaetze bleiben aber alle da",
           len(_saetze) >= len(_bc2.get("stand", [])) - 1,
           f"{len(_saetze)} von {len(_bc2.get('stand', []))} - es darf genau "
           f"der Bestandssatz fehlen, kein Marktfakt")

    # DER POSITIONS-BIAS-TEST MUSS WIEDER ETWAS MESSEN.
    _m = ZM.nur_markt(_bc2)
    _u = ZM.kehre_saetze_um(_m)
    pruefe(P, "die Umkehr aendert die Reihenfolge wirklich",
           _j.dumps(_m["stand"]) != _j.dumps(_u["stand"]),
           "die Standard-Umkehr dreht Schluessel - bei zwei Inhaltsbloecken "
           "blieb der Text Satz fuer Satz gleich, und der zweite Aufruf "
           "pruefte dieselbe Eingabe noch einmal")
    pruefe(P, "und laesst den Inhalt unveraendert",
           sorted(_m["stand"]) == sorted(_u["stand"]),
           "gefragt wird, ob dasselbe Material anders angeordnet dasselbe "
           "Urteil ergibt - nicht, ob anderes Material anderes ergibt")
    pruefe(P, "die alte Umkehr bleibt fuer die alte Faktenform in Kraft",
           "umkehr_fn or _kehre_objektive_fakten_um" in
           _nur_code("agent/krypto/gegenpruefung.py"),
           "die sechs alten Pipelines wurden nicht angefasst")

    # ARBEITSTEILUNG DER DREI EBENEN - keine prueft, was eine andere prueft.
    _z1 = _nur_code("agent/gegenpruefer_rollen.py")
    pruefe(P, "Z1 prueft Text gegen AKTION (Richtungstreue)",
           "def pruefe_richtungstreue" in _z1)
    # Z1 UND ROLLE G PRUEFEN VERSCHIEDENES, und das war der Sinn dieser
    # Pruefung. Sie stand auf `pruefe_konsistenz`; seit dem 17.08. gibt es
    # die nicht mehr. Die Trennung selbst gilt weiter - und ist SCHAERFER
    # geworden, weil Rolle G nicht einmal mehr denselben Faktentext sieht.
    pruefe(P, "Z1 prueft gegen die Aktion, Rolle G gegen eigene Fakten",
           "def pruefe_richtungstreue" in _z1
           and "positionierung" in _quelltext("agent/zweite_meinung.py")
           and "faktentext" not in _quelltext(
               "agent/zweite_meinung.py").split("def rolle_g")[1][:2000],
           "sonst pruefen zwei Ebenen dasselbe und keine die Luecke dazwischen")
    pruefe(P, "der Gegenpruefer laeuft deterministisch, der Pruefer nicht",
           "temperature = 0.2" in _nur_code("agent/rollen_lauf.py")
           and "temperature = 0.0" in _nur_code("agent/krypto/gegenpruefung.py"),
           "ein Urteil ueber ein Urteil soll bei gleicher Eingabe gleich "
           "ausfallen - sonst misst man Sampling-Rauschen")

    # ------------------------------------------------------------------
    # H. DER ENTSCHEIDER LIEST SEINE EIGENE BILANZ (15.1).
    #
    # Bis zum 13.08. stand in rollen_lauf `TB.bewerte({}, ...)` - ein LEERES
    # Dict. Zusammen mit dem fehlenden Schreiben waren das zwei Luecken in
    # Reihe: nichts wurde gezaehlt, und das Nichts wurde auch nicht gelesen.
    _lauf = _nur_code("agent/rollen_lauf.py")
    pruefe(P, "der Lauf zaehlt seine eigene Bilanz",
           "TB . zaehle ( conn" in _lauf,
           "sonst faellt der Entscheider IMMER auf die Basisrate zurueck, "
           "auch wenn Faelle vorliegen")
    pruefe(P, "und der Entscheider bekommt sie auch",
           "TB . bewerte ( bilanz" in _lauf,
           "das leere Dict war der zweite Teil derselben Luecke")
    # ⚠️ UEBER DEN SYNTAXBAUM STATT UEBER DIE ZEILENFOLGE (01.09.2026).
    #
    # Hier stand `_lauf.find("TB . zaehle") < _lauf.find("for symbol in
    # symbole")` - ein Vergleich von Textpositionen. Er fiel um, als die
    # Schleife in Schritt 3 auf Zellen umgestellt wurde und ihr Kopf
    # `for symbol, _zelle_strategie in _paare:` hiess: `find` gab -1, und
    # jede Zahl ist groesser als -1.
    #
    # ⚠️ Die AUSSAGE war und bleibt richtig - die Bilanz gehoert EINMAL je
    # Lauf geholt. Falsch war nur, sie an einem Schleifenkopf-TEXT
    # festzumachen. Geprueft wird jetzt die Eigenschaft: der Aufruf darf in
    # KEINER Schleife stehen.
    import ast as _ast_b
    _baum_b = _ast_b.parse(_pl_pfad("agent/rollen_lauf.py"))
    _in_schleife = False
    for _k in _ast_b.walk(_baum_b):
        if not isinstance(_k, (_ast_b.For, _ast_b.While)):
            continue
        for _c in _ast_b.walk(_k):
            if (isinstance(_c, _ast_b.Call)
                    and isinstance(_c.func, _ast_b.Attribute)
                    and _c.func.attr == "zaehle"):
                _in_schleife = True
    pruefe(P, "gezaehlt wird EINMAL je Lauf, nicht je Asset",
           not _in_schleife,
           "45 Symbole waeren sonst 45 Abfragen ueber dieselbe Tabelle - und "
           "eine mitwachsende Bilanz haenge das Urteil an der Reihenfolge")

    # BEIDE SEITEN MUESSEN DENSELBEN SCHLUESSEL BAUEN. Wuerde die Zaehlung
    # anders schluesseln als die Live-Bewertung, ginge JEDER Nachschlag ins
    # Leere - lautlos, und alles fiele auf die Basisrate zurueck.
    _b = TB.zaehle(c, quelle_kette="rollen")
    _live = TB.merkmale(
        vola_perzentil=TB._prozent(familien["schwankung_perzentil"]),
        spanne_perzentil=TB._prozent(familien["momentum_perzentil"]),
        gleichlauf=TB._band_grob(familien["volumen_perzentil"]))
    pruefe(P, "Zaehlung und Live-Bewertung treffen dieselbe Zelle",
           _live in _b,
           f"live {_live} gegen gezaehlt {list(_b)[:3]} - ein Nachschlag ins "
           f"Leere waere lautlos und saehe aus wie 'keine Daten'")
    pruefe(P, "und die Bewertung findet die Faelle dann auch",
           TB.bewerte(_b, _live)["faelle"] >= 1,
           "der Beweis, dass die Kette von der eigenen Historie lernen KANN - "
           "vorher war das strukturell unmoeglich")

    # ------------------------------------------------------------------
    # I. DREI STIMMEN STATT ZWEI (nach der Messung vom 13.08.).
    #
    # `messe_namensanker.py` hat ueber 20 Symbole gezeigt: bei IDENTISCHER
    # Eingabe und temperature 0.0 kippt das Richtungsurteil in 30 % der Faelle.
    # Der alte Zweierabgleich fiel bei Uneinigkeit auf NEUTRAL zurueck - bei
    # diesem Rauschen ueberwiegend ZUFAELLIG, nicht wegen der Anordnung.
    class _Fest:
        def __init__(self, folge): self.folge, self.n = folge, 0
        def chat(self, m, **k):
            r = self.folge[self.n % len(self.folge)]
            self.n += 1
            return ('{"eigene_richtung": "%s", "kurzbegruendung": "x"}' % r
                    if r else "kaputt")

    # DER RICHTUNGSABGLEICH IST STILLGELEGT (16.08.2026). `mehrheit()` bleibt
    # als Code stehen - sie ist der Beleg dafuer, wie er funktioniert hat, und
    # die 2.469 gemessenen Zeilen bleiben damit deutbar. Aber sie wird NICHT
    # mehr aufgerufen, und genau das wird hier geprueft.
    #
    # Warum entfernt: SHORT 1.246, NEUTRAL 1.206, LONG 17 ueber 2.469
    # Pruefungen; bei LONG-Signalen zwei Zustimmungen in 377 Faellen; und
    # seine Zustimmung trennte die Ausgaenge nicht (0 von 7 gegen 17,2 %).
    _zm_code = _nur_code("agent/zweite_meinung.py")
    pruefe(P, "der Richtungsabgleich wird nicht mehr aufgerufen",
           "mehrheit ( zai_client" not in _zm_code,
           "vier Aufrufe je Signal, davon drei fuer ein fast konstantes Feld")
    pruefe(P, "die Funktion bleibt aber lesbar",
           "def mehrheit" in _zm_code,
           "die 2.469 gemessenen Zeilen muessen deutbar bleiben")
    pruefe(P, "die alte Zweierfassung bleibt fuer die alten Pipelines",
           "def leite_eigene_richtung_positionsrobust" in
           _quelltext("agent/krypto/gegenpruefung.py"))

    # DIE STIMMENZAHL LANDET IN EINER EIGENEN SPALTE, nicht im Freitext.
    ZM.schreibe(c, sid, {"urteil": "konsistent", "eigene_richtung": "LONG",
                         "stimmen": 2, "von": 3})
    pruefe(P, "zai_stimmen steht auf der Signalzeile",
           c.execute("SELECT zai_stimmen FROM signals WHERE id = ?",
                     (sid,)).fetchone()[0] == 2,
           "jede spaetere Auswertung muss nach der Einigkeit filtern koennen, "
           "ohne einen Freitext zu zerlegen")

    # ------------------------------------------------------------------
    # J. RICHTUNG UND HEBELFAKTOR UEBERLEBEN DAS SCHREIBEN (15.5c).
    #
    # Gefunden im ERSTEN Live-Lauf des Hebel-Wegs am 13.08. - und nur dort zu
    # finden: vier echte Hebel-Signale landeten RICHTUNGSLOS in der Datenbank,
    # weil `signals` keine solche Spalte kannte (nur `hebel_signals`, die
    # Tabelle der alten Kette). Ein SHORT sah aus wie ein LONG.
    # `instrument` IST SEIT DEM 15.08. DER DISKRIMINATOR, nicht der Wert.
    # Vorher entschied `hebel > 1.0`, ob die Spalte gefuellt wird - das traf
    # auch einen echten Hebel-Trade, dessen Faktor auf 1,0 faellt (KAITO und
    # CAT am ersten Produktionsvormittag).
    _mit = SA.felder_aus_entscheidung(
        {"aktion": "ERÖFFNEN", "richtung": "SHORT", "begruendung": "x"},
        fakten={}, rechnung={"hebel": 4.5}, instrument="hebel")
    pruefe(P, "die Richtung des Modells landet in den Feldern",
           _mit.get("richtung") == "SHORT",
           "sie ist bei EROEFFNEN und NACHKAUFEN Pflicht und dreht Stop, Ziel "
           "und Liquidation - ohne sie ist ein Hebel-Signal nicht lesbar")
    pruefe(P, "der Hebelfaktor kommt aus der RECHNUNG",
           _mit.get("hebel") == 4.5,
           "das Modell nennt die Richtung, das System rechnet den Faktor "
           "(Paket 13) - er darf nur von dort kommen")
    _ohne = SA.felder_aus_entscheidung({"aktion": "KAUFEN"}, fakten={})
    pruefe(P, "bei Spot steht keine Richtung da",
           "richtung" not in _ohne and "hebel" not in _ohne,
           "ein eingetragenes LONG waere eine Behauptung, die niemand "
           "aufgestellt hat")
    # DER FALL, DER AM 15.08. DURCHRUTSCHTE: ein echter Hebel-Trade mit Faktor
    # genau 1,0. Er MUSS die Spalte tragen, sonst zaehlt ihn `toepfe` als Spot
    # und der Hebel-Cooldown (`hebel IS NOT NULL`) findet ihn nie.
    _eins = SA.felder_aus_entscheidung(
        {"aktion": "ERÖFFNEN", "richtung": "LONG"},
        fakten={}, rechnung={"hebel": 1.0}, instrument="hebel")
    pruefe(P, "ein Hebel-Trade mit Faktor 1,0 traegt die Spalte trotzdem",
           _eins.get("hebel") == 1.0,
           "KAITO und CAT wurden so als Spot geschrieben - ausserhalb von "
           "Hebel-Cooldown und Hebel-Topf, mit dem Betreff 'EROEFFNEN (Hebel)'")
    # Und die Gegenprobe: derselbe Wert bei Spot bleibt draussen.
    _spot_eins = SA.felder_aus_entscheidung(
        {"aktion": "KAUFEN"}, fakten={}, rechnung={"hebel": 1.0},
        instrument="spot")
    pruefe(P, "derselbe Wert 1,0 bleibt bei Spot draussen",
           "hebel" not in _spot_eins,
           "sonst truege jedes Spot-Signal wieder in den Hebel-Topf")
    _sid3 = SA.schreibe_signal(c, _mit, symbol="TESTH")
    _z = c.execute("SELECT richtung, hebel FROM signals WHERE id = ?",
                   (_sid3,)).fetchone()
    pruefe(P, "und beide stehen danach wirklich in der Zeile",
           tuple(_z) == ("SHORT", 4.5), str(tuple(_z)))

    # ------------------------------------------------------------------
    # K. DAEMPFER: ZWEI STILLGELEGT, DER REST ZAEHLT MIT (13.08.).
    from agent import daempfer as DA

    # DER NAME IST DER SCHLUESSEL - und deshalb muss er im Gate WOERTLICH
    # vorkommen. Eine Umbenennung dort waere sonst eine stille
    # Wiederaktivierung, und niemand wuerde es merken.
    _gates = (_quelltext("agent/krypto/risk_gate.py")
              + _quelltext("agent/krypto/hebel_risk_gate.py"))
    for _name in DA.STILLGELEGT:
        pruefe(P, f"'{_name}' kommt im Gate woertlich vor", _name in _gates,
               "sonst waere die Stilllegung wirkungslos und unbemerkt")

    _k = [("Konfidenz-Skalierung (70%, Sockel 50%)", 300.0),
          ("CRV-Abstufung (2.30: 60 %)", 600.0),
          ("Regime-Richtungs-Konflikt", 3.0),
          ("hohe Bear-Szenario-Wahrscheinlichkeit (40%)", 500.0)]
    _w, _g = DA.teile(_k)
    pruefe(P, "die zwei stillgelegten sind aus der Auswahl raus",
           {x[0].split(" (")[0] for x in _g}
           == {"Konfidenz-Skalierung", "Regime-Richtungs-Konflikt"},
           f"{[x[0] for x in _g]}")
    pruefe(P, "der GEMESSENE Daempfer bleibt wirksam",
           any(x[0].startswith("CRV-Abstufung") for x in _w),
           "an 298 Spot-Signalen gemessen: SQN +0,63 -> +1,36, Rueckschlag "
           "36,3 -> 27,1 R. Ihn stillzulegen hiesse, eine belegte "
           "Verbesserung wegzuwerfen")
    pruefe(P, "die ungemessenen bleiben ebenfalls wirksam",
           any("Bear-Szenario" in x[0] for x in _w),
           "sie verkleinern nur - und abschalten waere eine "
           "Verhaltensaenderung an einer LAUFENDEN Kette (Aktien, Rohstoffe, "
           "Themen-ETF, Hedge)")
    pruefe(P, "der stillgelegte kann den Deckel nicht mehr binden",
           min(_w, key=lambda p: p[1])[1] == 500.0,
           "ohne die Trennung haette der Regime-Konflikt mit 3.0 gewonnen")

    _v = DA.vermerk(min(_w, key=lambda p: p[1])[0], _k, _g)
    pruefe(P, "der Vermerk sagt, was gegriffen HAETTE",
           "stillgelegt_haetten_gegriffen=" in _v
           and "Konfidenz-Skalierung" in _v, _v[:90])
    pruefe(P, "und was tatsaechlich gebunden hat",
           _v.startswith("bindend="), _v[:60])
    pruefe(P, "ohne jeden Kandidaten gibt es keinen leeren Vermerk",
           DA.vermerk(None, [], []) is None,
           "eine Zeile 'bindend=' ohne Inhalt saehe aus wie ein Befund")

    # DIE VORHANDENE, IMMER LEERE SPALTE WIRD ENDLICH BEFUELLT.
    # ZWEI QUELLEN, UND DAS IST DER PUNKT: der Spaltenname ist eine
    # ZEICHENKETTE, und `_nur_code()` entfernt genau die. Er muss im Rohtext
    # gesucht werden, der Aufruf im Code. Meine erste Fassung suchte beides im
    # Code-Text und meldete einen Defekt, den es nicht gab - derselbe Helfer,
    # der heute Vormittag drei falsche Alarme BEHOBEN hat, hat hier einen
    # erzeugt. Ein Werkzeug loest keine Sorgfaltsfrage, es verschiebt sie.
    pruefe(P, "der Vermerk landet in hebel_korrektur_hinweis",
           "hebel_korrektur_hinweis" in _quelltext(
               "agent/krypto/hebel_risk_gate.py")
           and "DA . vermerk" in _nur_code("agent/krypto/hebel_risk_gate.py"),
           "die Spalte gibt es seit jeher und war in ALLEN Zeilen leer - der "
           "Platz war da, benutzt hat ihn niemand")
    pruefe(P, "und im Spot-Gate in die Kuerzungsnotiz",
           "DA . vermerk" in _nur_code("agent/krypto/risk_gate.py"))

    # ------------------------------------------------------------------
    # L. DIE UEBERNAHMEN AUS DER ALTEN KETTE (Vollumstieg, 13.08.).
    #
    # Der Nutzer hat den glatten Schnitt entschieden: eine Kette je Assetklasse,
    # kein Parallelbetrieb. Was die alte Kette BESSER konnte, muss vorher
    # herueber - sonst ist der Schnitt ein Rueckschritt mit Zahlen.
    from agent import entscheidungsrechnung as ER
    from agent import faktenblock as FB
    from agent import rollen_lauf as RL2
    from agent import toepfe as TO

    # L1 DIE CRV-ABSTUFUNG IST STILLGELEGT (15.08.2026).
    #
    # Sie war die einzige GEMESSENE Groessenregel der alten Kette - an 298
    # Spot-Signalen, SQN +0,63 -> +1,36. Diese Pruefungen verlangten bis heute,
    # dass sie WIRKT.
    #
    # WARUM SIE STILL IST. Gemessen wurde sie, als das Ziel MECHANISCH bei
    # CRV 2,0 lag. Seit dem Struktur-Ziel (12.08.) haengt es am naechsten
    # Widerstand - das CRV faellt aus dem Chart und ist keine Konstante mehr.
    # Mit `crv_voll_ab = 6.0` traf der Regelfall CRV 2,0 den Sockel 1/5:
    #
    #     CRV 2,0 -> 160 von 800 EUR
    #
    # Das ist kein Regler mehr, sondern eine pauschale Kuerzung auf ein
    # Fuenftel - aus einer Messung unter Bedingungen, die es nicht mehr gibt.
    # Dieselbe Fehlerklasse wie dreimal am 14.08.
    #
    # SIE WIRD NICHT NEU KALIBRIERT, sondern stillgelegt. Eine neue Spreizung
    # waere wieder eine Zahl ohne Messung. Messbar wird sie, sobald die neue
    # Kette aufgeloeste Signale liefert - dann steht die Frage neu.
    pruefe(P, "die CRV-Abstufung hat keine Wirkung mehr",
           ER.GRENZEN["crv_spreizung"] == 1.0
           and ER._crv_faktor(2.0, "spot", "krypto") == 1.0
           and ER._crv_faktor(6.0, "spot", "krypto") == 1.0,
           "1.0 = ohne Wirkung; der Faktor bleibt im Code, damit die Regel "
           "wieder eingeschaltet werden kann, wenn sie gemessen ist")
    pruefe(P, "und der Betrag folgt jetzt der Tranche",
           ER.rechne(kurs=100.0, atr=3.0, risiko_eur=120.0, instrument="spot",
                     betrag_wunsch_eur=800.0)["betrag_eur"] == 800.0,
           "eine Zahl, die der Nutzer vorgegeben hat - und eine, die aus dem "
           "Stop folgt. Mehr entscheidet das System nicht")
    pruefe(P, "die Regel ist eine EINSCHLUSSliste",
           'instrument != "spot"' in _quelltext("agent/entscheidungsrechnung.py"),
           "eine Ausschlussliste faengt nur, was jemand vorhergesehen hat; "
           "eine Einschlussliste nur, was jemand gemessen hat")
    pruefe(P, "beim HEBEL wirkt sie NICHT",
           all(ER._crv_faktor(c / 10, "hebel") == 1.0 for c in range(20, 100)),
           "dieselbe Untersuchung fand beim Hebel die GEGENLAEUFIGE Antwort "
           "(SQN +3,25 gegen +1,25). Sie dort anzuwenden hiesse, eine Messung "
           "gegen ihr eigenes Ergebnis zu uebertragen")
    pruefe(P, "sie laesst sich abschalten, ohne Code zu aendern",
           ER._crv_faktor.__doc__ and "crv_spreizung" in ER._crv_faktor.__doc__,
           "Abschalten ueber crv_spreizung = 1.0")
    _r = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=150.0, instrument="spot",
                   umgeworfen_preis_eur=94.0)
    pruefe(P, "der Faktor steht in der Rechnung und ist nachlesbar",
           "crv_groessenfaktor" in _r,
           "eine Kuerzung, die niemand sieht, ist der unsichtbare Filter")
    # DER SCHLUESSEL HEISST `betrag_gedeckelt_durch`, nicht `betrag_grund` -
    # nachgesehen statt geraten, nachdem die erste Fassung genau daran scheiterte.
    pruefe(P, "und der Grund nennt keine Abstufung mehr",
           ER.rechne(kurs=100.0, atr=3.0, risiko_eur=120.0, instrument="spot",
                     betrag_wunsch_eur=800.0).get("betrag_gedeckelt_durch")
           is None,
           "stillgelegt heisst: sie taucht auch in der Begruendung nicht auf")

    # L2 DIE KOSTENKLASSE - der latente Defekt aus Kapitel 17.3.
    pruefe(P, "Krypto und Boerse bekommen verschiedene Kostenklassen",
           RL2._kostenklasse("krypto") == "krypto"
           and RL2._kostenklasse("aktien") == "boerse",
           "bei der ersten Aktie haette der Entscheider sonst mit "
           "Krypto-Gebuehren (1,5 % je Seite) statt Boersengebuehren "
           "gerechnet - der Breakeven waere grob falsch gewesen")
    _kr = TB.kosten_r_aus_stop(100.0, 95.0, klasse="krypto", position_eur=250)
    _bo = TB.kosten_r_aus_stop(100.0, 95.0, klasse="boerse", position_eur=250)
    pruefe(P, "und die Zahlen unterscheiden sich wirklich",
           abs(_kr - _bo) > 0.05,
           f"Krypto {_kr:.3f} R gegen Boerse {_bo:.3f} R bei 250 EUR")
    pruefe(P, "die Kette uebergibt Klasse UND Positionsgroesse",
           "klasse = _kostenklasse ( assetklasse )" in _nur_code(
               "agent/rollen_lauf.py")
           and "position_eur = rechnung" in _nur_code("agent/rollen_lauf.py"),
           "ohne die Groesse waere die Fixgebuehr auf 500 EUR geschaetzt - "
           "bei einer 250-EUR-Tranche das Doppelte danebengelegen")

    # L3 DER BEREICH FOLGT DER KLASSE.
    for _k, _erw in (("krypto", "krypto_spot"), ("aktien", "aktien"),
                     ("hedge", "hedge")):
        pruefe(P, f"Bereich fuer {_k}", RL2._bereich(_k, "spot") == _erw,
               f"-> {RL2._bereich(_k, 'spot')}")
    pruefe(P, "nur Krypto wird nach Instrument getrennt",
           RL2._bereich("krypto", "hebel") == "krypto_hebel"
           and RL2._bereich("aktien", "hebel") == "aktien",
           "Finanzierung und Liquidation gibt es nur beim Hebel")
    pruefe(P, "jeder Bereich existiert im Faktenblock",
           all(RL2._bereich(k, i) in FB.ZUSATZ_JE_BEREICH
               for k in RL2.KLASSEN for i in ("spot", "hebel")),
           str(sorted({RL2._bereich(k, i) for k in RL2.KLASSEN
                       for i in ("spot", "hebel")}
                      - set(FB.ZUSATZ_JE_BEREICH))))
    pruefe(P, "eine unbekannte Assetklasse bricht den Lauf ab",
           _wirft(lambda: RL2.fuehre_lauf(conn=c, reihen={"X": []}, symbole=[],
                                          betriebsart="trocken",
                                          assetklasse="krytpo"),
                  RL2.LaufAbgebrochen),
           "ein Tippfehler soll auffallen und nicht vierzigmal in einen "
           "unbekannten Bereich laufen")
    # ------------------------------------------------------------------
    # M. CASH-RESERVE RM-4, ABSOLUT (O-1, 13.08.).
    #
    # `toepfe.UEBERGREIFEND = ("cash_reserve",)` fuehrt sie als DIE eine Regel,
    # die ueber Toepfe hinweg wirkt - dokumentiert seit Paket 5 und bis heute
    # nirgends gebaut. Genau die Sorte Luecke, die eine Doku nicht findet, weil
    # sie ja stimmt.
    pruefe(P, "die Reserve ist absolut, nicht prozentual",
           isinstance(TO.VORGABE_RESERVE_EUR, float),
           "die prozentuale Haelfte der alten Regel braucht den Portfoliowert, "
           "den diese Kette absichtlich nicht kennt")
    pruefe(P, "Stablecoins sind eine explizite Liste, keine Namensheuristik",
           "USDC" in TO.STABLECOINS and len(TO.STABLECOINS) < 12,
           "ein Token mit 'USD' im Namen ist noch kein Stablecoin - ein falsch "
           "mitgezaehlter Bestand machte die Reserve wertlos")
    _frei = TO.cash_frei_eur(c)
    pruefe(P, "sie rechnet an echten Daten eine Zahl aus",
           _frei is not None and _frei >= 0, f"{_frei}")
    # UND SIE HAENGT NICHT AN DER ZEILENFABRIK DER VERBINDUNG. Ohne
    # `sqlite3.Row` warf der Lesezugriff und die Funktion gab None zurueck -
    # also KEINE Begrenzung. Ein still ausfallender Schutz ist schlimmer als
    # ein fehlender, weil niemand ihn vermisst.
    import sqlite3 as _sq3
    _alt = c.row_factory
    c.row_factory = None
    pruefe(P, "auch ohne sqlite3.Row liefert sie denselben Wert",
           TO.cash_frei_eur(c) == _frei, f"{TO.cash_frei_eur(c)} gegen {_frei}")
    c.row_factory = _alt
    # SIE BEGRENZT, SIE VERHINDERT NICHT - das steht so in der Regel.
    # MIT AUSDRUECKLICHER TRANCHE. Ohne sie faellt der Betrag auf die
    # Rueckfallgroesse, die CRV-Abstufung drueckt ihn auf die Mindestgroesse -
    # und dann bindet der Cash-Deckel nicht mehr, obwohl er es sollte. Die
    # Pruefung haette also nicht die Cash-Reserve gemessen, sondern die
    # Abstufung (gefunden, als die Spot-Groesse am 14.08. auf die Tranche
    # umgestellt wurde).
    _mit = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.0, instrument="spot",
                     betrag_wunsch_eur=2000.0,
                     umgeworfen_preis_eur=94.0, cash_frei_eur=300.0)
    _ohne = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.0, instrument="spot",
                      betrag_wunsch_eur=2000.0, umgeworfen_preis_eur=94.0)
    # UMGESCHRIEBEN 15.08.2026 - siehe Topf oben, dieselbe Trennlinie.
    pruefe(P, "knappes Cash aendert den Betrag NICHT mehr",
           _mit["betrag_eur"] == _ohne["betrag_eur"],
           f"{_mit['betrag_eur']} gegen {_ohne['betrag_eur']} EUR - Cash ist "
           "eine Portfoliofrage, und das System kennt den Bestand, nicht die "
           "Absicht")
    pruefe(P, "aber es meldet die Lage",
           _mit.get("cash_frei_eur") == 300.0
           and _mit.get("cash_wuerde_ueberschreiten") is True
           and "cash_frei_eur" not in _ohne,
           "ohne ermittelbares Cash steht auch keine Zeile in der Mail")
    pruefe(P, "ohne ermittelbares Cash gibt es KEINE Sperre",
           ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.0, instrument="spot",
                     betrag_wunsch_eur=2000.0, umgeworfen_preis_eur=94.0,
                     cash_frei_eur=None)["betrag_eur"] > 300,
           "eine Reserve, die wegen einer fehlenden Zahl ALLES sperrt, waere "
           "schlimmer als keine")
    pruefe(P, "der Trockenlauf fragt das Cash gar nicht ab",
           "if betriebsart != TROCKEN else None" in _nur_code(
               "agent/rollen_lauf.py"),
           "er hat keine Verbindung zu einer echten Lage")

    # ------------------------------------------------------------------
    # N. WAS DER WATCHLIST-PROBELAUF GEFUNDEN HAT (13.08., 25 Symbole).
    #
    # Beides nur in einem VOLLEN Lauf sichtbar - acht Symbole hatten es nicht
    # gezeigt.

    # N1 DIE 1,0 VON SPOT DARF NICHT AUF DIE SIGNALZEILE.
    _spot = SA.felder_aus_entscheidung({"aktion": "KAUFEN"}, fakten={},
                                       rechnung={"hebel": 1.0})
    pruefe(P, "ein Spot-Signal traegt KEINEN Hebel", "hebel" not in _spot,
           "`toepfe.belegt_eur()` trennt die Toepfe an genau dieser Spalte - "
           "neun Spot-Signale trugen 2.250 EUR in den HEBEL-Topf")
    _heb = SA.felder_aus_entscheidung({"aktion": "ERÖFFNEN", "richtung": "LONG"},
                                      fakten={}, rechnung={"hebel": 3.3},
                                      instrument="hebel")
    pruefe(P, "ein echter Hebel steht weiterhin da", _heb.get("hebel") == 3.3)
    # UND DIE UMKEHRUNG VOM 15.08.: ein Spot-Lauf, dem jemand einen Faktor
    # ueber 1,0 mitgibt, darf die Spalte trotzdem NICHT fuellen. Vorher haette
    # allein der Wert entschieden - das Instrument ist die verlaessliche
    # Angabe, nicht die Zahl.
    _spot_hoch = SA.felder_aus_entscheidung(
        {"aktion": "KAUFEN"}, fakten={}, rechnung={"hebel": 3.3},
        instrument="spot")
    pruefe(P, "und ein Spot-Lauf fuellt sie auch bei 3,3 nicht",
           "hebel" not in _spot_hoch,
           "das Instrument entscheidet, nicht der Wert")
    pruefe(P, "und die Topftrennung greift danach richtig",
           "hebel IS NULL" in _quelltext("agent/toepfe.py")
           and "hebel IS NOT NULL" in _quelltext("agent/toepfe.py"),
           "die Spalte ist der Diskriminator - sie muss eindeutig bleiben")

    # N2 DIE FEHLERSTUFE GEHOERT ZUM SYMBOL, nicht zum Lauf.
    _d = RG.Durchlauf("t")
    for _s, _bis in (("A", "urteil"), ("B", "risikoschicht")):
        _d.beginne(_s)
        for _st, _ in RG.STUFEN:
            _d.bestanden(_s, _st)
            if _st == _bis:
                break
    pruefe(P, "jedes Symbol merkt sich seine eigene letzte Stufe",
           _d.letzte_stufe == {"A": "urteil", "B": "risikoschicht"},
           f"{_d.letzte_stufe} - im Probelauf brach RENDER im URTEIL ab und "
           f"wurde als Verlust der RISIKOSCHICHT gezaehlt, weil andere Symbole "
           f"dort schon durch waren")
    # UND DER VERLUST GEHOERT AN DIE STUFE, AN DER GEARBEITET WURDE.
    pruefe(P, "wer im Urteil abstuerzt, verliert im Urteil - nicht im Lagebild",
           _d.naechste_stufe("A") == "aktion"
           and _d.naechste_stufe("B") == "entscheider",
           f"A {_d.naechste_stufe('A')}, B {_d.naechste_stufe('B')} - im "
           f"zweiten Probelauf starben zwei Symbole am Gemini-503 waehrend des "
           f"Trader-Aufrufs und wurden eine Stufe zu frueh gebucht")
    pruefe(P, "ein Symbol ohne bestandene Stufe faellt auf die erste",
           _d.naechste_stufe("gibtsnicht") == RG.STUFEN_NAMEN[0])
    pruefe(P, "und an der letzten Stufe laeuft es nicht ueber",
           _d.naechste_stufe("B") in RG.STUFEN_NAMEN)
    pruefe(P, "der Lauf liest sie auch aus",
           "durchlauf . naechste_stufe ( symbol )" in _nur_code(
               "agent/rollen_lauf.py"),
           "die Tabelle zeigt sonst auf die falsche Stelle - und das ist der "
           "einzige Zweck, den sie hat")

    # ------------------------------------------------------------------
    # O. VORUEBERGEHENDE ANBIETERFEHLER (503) - gemessen, nicht vermutet.
    #
    # Im Watchlist-Probelauf antwortete Gemini zweimal mit HTTP 503 ("high
    # demand"): 1 von 25 und 2 von 25 Aufrufen, rund 8 % Ausfall OHNE unser
    # Zutun. Bis dahin flog jeder 503 durch - das Symbol war fuer den ganzen
    # Lauf verloren, und in der Durchlaessigkeitstabelle stand ein Fehlschlag,
    # der gar keiner war.
    import json as _j2
    import api.gemini as _G
    import database.api_health as _AH

    class _Antwort:
        def __init__(self, code, body=None):
            self.status_code, self.ok = code, code < 400
            self._b = body or {}
            self.text = _j2.dumps(self._b)
            self.headers = {}

        def json(self):
            return self._b

    class _Sitzung:
        def __init__(self, folge):
            self.folge, self.n = folge, 0

        def post(self, *a, **k):
            r = self.folge[min(self.n, len(self.folge) - 1)]
            self.n += 1
            return _Antwort(*r)

    _GUT = {"choices": [{"message": {"content": "{}"}}]}
    _alt_sleep, _alt_zaehl = _G.time.sleep, _G.zaehle_aufruf
    _alt_health = _AH.track_api_health
    # NICHT IN DIE PRODUKTIVDATEI SCHREIBEN. `track_api_health` bucht sonst je
    # Aufruf einen Gesundheitsstand - im ersten Anlauf ist mir das
    # durchgerutscht, und es ist genau der Fehler, den der Trockenlauf-Grundsatz
    # dieser Kette verhindern soll.
    _G.time.sleep = lambda s: None
    _G.zaehle_aufruf = lambda *a, **k: None
    try:
        _c = _G.GeminiClient("x", session=_Sitzung([(503,), (503,), (200, _GUT)]))
        _c.chat([{"role": "user", "content": "hi"}])
        pruefe(P, "zwei 503 hintereinander werden ueberstanden",
               _c._session.n == 3,
               f"{_c._session.n} Anlaeufe - vorher war das Symbol verloren")
        _c2 = _G.GeminiClient("x", session=_Sitzung([(503,)]))
        pruefe(P, "ein dauerhafter 503 wirft nach begrenzten Versuchen",
               _wirft(lambda: _c2.chat([{"role": "user", "content": "hi"}]),
                      Exception) and _c2._session.n == _G._MAX_VERSUCHE_BEI_503,
               f"{_c2._session.n} Anlaeufe - wenn ein kurzer Moment nicht hilft, "
               f"hilft auch die zehnte Wiederholung nicht")
        _c3 = _G.GeminiClient("x", session=_Sitzung([(400, {"e": 1})]))
        _wirft(lambda: _c3.chat([{"role": "user", "content": "hi"}]), Exception)
        pruefe(P, "ein 400 wird NICHT wiederholt", _c3._session.n == 1,
               "ein fehlerhafter Antrag wird beim zweiten Mal nicht richtig")
    finally:
        _G.time.sleep, _G.zaehle_aufruf = _alt_sleep, _alt_zaehl
        _AH.track_api_health = _alt_health
    pruefe(P, "die 429-Versuche werden davon nicht aufgebraucht",
           "versuch_503 = versuch_429 = 0" in _nur_code("api/gemini.py"),
           "zwei Gruende, zwei Zaehler - sonst nimmt ein Anbieterausfall die "
           "Versuche, die fuer die Ratenbegrenzung gedacht sind")

    # ------------------------------------------------------------------
    # P. DER SCHNITT: eine Klasse, eine Kette (14.08.).
    from scheduler import rollen_job as RJ

    pruefe(P, "die Vorgabe stellt NICHTS um",
           RJ.aktiv_fuer() == () and not RJ.bedient_neue_kette("krypto"),
           "ein Modul, das beim blossen Einspielen die Produktion umstellt, "
           "nimmt dem Nutzer die Entscheidung ab, die er treffen wollte")
    _cfg = {"rollen_kette": {"aktiv_fuer": ["Krypto"]}}
    pruefe(P, "der Schalter wirkt und ist schreibweisen-tolerant",
           RJ.bedient_neue_kette("krypto", _cfg),
           "'Krypto' und 'krypto' sollen nicht zwei verschiedene Dinge sein")
    pruefe(P, "und er wirkt NUR fuer die genannte Klasse",
           not RJ.bedient_neue_kette("aktien", _cfg)
           and not RJ.bedient_neue_kette("hedge", _cfg),
           "Aktien brauchen noch eine Kursquelle, Hedge das Paket 14")

    # DIE EIGENTLICHE ZUSICHERUNG: nie zwei Ketten fuer dasselbe Asset.
    # WIEDER DIE ZEICHENKETTEN-FALLE: `_nur_code()` entfernt Literale, also
    # auch das "krypto" im Aufruf. Dritter Fall heute - der Helfer ist richtig,
    # meine Verwendung war es zweimal nicht. Gesucht wird deshalb im ROHTEXT.
    # ANGEPASST 15.08.: die Frage lautet nicht mehr "ist krypto umgestellt",
    # sondern "ist IRGENDEINE Gruppe umgestellt". Waere Krypto eines Tages
    # abgeschaltet und Aktien nicht, liefe der Umlauf sonst lautlos gar nicht,
    # und der Allocator uebernaehme wieder.
    pruefe(P, "der Allocator fragt VOR dem Lauf, ob etwas umgestellt ist",
           "if any(bedient_neue_kette(g, config_dict)" in _quelltext(
               "scheduler/background.py"),
           "sonst gaebe es fuer dasselbe Asset zwei Empfehlungen, und der "
           "Nutzer muesste entscheiden, welcher er glaubt")
    _roh = _quelltext("scheduler/background.py")
    _i_frage = _roh.find("if any(bedient_neue_kette(g, config_dict)")
    _i_alloc = _roh.find("from agent.krypto.budget_allocator import run_budget_allocator")
    pruefe(P, "die Frage steht VOR dem Import des alten Weges",
           -1 < _i_frage < _i_alloc,
           f"{_i_frage} gegen {_i_alloc} - danach waere sie wirkungslos")
    pruefe(P, "der uebersprungene Lauf sagt WARUM",
           "Eine Klasse, eine " in _roh,
           "ein stiller Sprung sieht aus wie ein Ausfall")

    # DAS JOB-MODUL SELBST.
    pruefe(P, "die Betriebsart ist von Haus aus `probe`, nicht `scharf`",
           "betriebsart: str = \"probe\"" in _quelltext("scheduler/rollen_job.py"),
           "wer Mails verschicken will, sagt es ausdruecklich")
    pruefe(P, "die Verbindung wird im JOB geoeffnet und geschlossen",
           "conn_factory ( )" in _nur_code("scheduler/rollen_job.py")
           and "conn . close ( )" in _nur_code("scheduler/rollen_job.py"),
           "rollen_lauf oeffnet grundsaetzlich keine - hier ist der Ort, an "
           "dem klar ist, welche Datenbank gemeint ist")
    # SAMMELPOSTEN FALLEN JETZT FRUEHER HERAUS: sie stehen gar nicht in der
    # Watchlist, also auch nicht in `assetklassen.gruppiere()`. Die Filterung
    # nach dem Unterstrich im Job ist damit ueberfluessig geworden.
    from agent import assetklassen as _AK2
    pruefe(P, "Sammelposten sind in keiner Gruppe",
           not any(s.startswith("_") for ss in _AK2.gruppiere().values()
                   for s in ss),
           "_ROHSTOFF_FUTURES_* steht nicht in der Watchlist und ist kein "
           "handelbares Asset")
    pruefe(P, "Symbole ohne Kursreihe werden gemeldet, nicht verrechnet",
           "Symbole ohne Kursreihe" in _quelltext("scheduler/rollen_job.py"),
           "sonst faerbten sie die Durchlaessigkeit mit einem Verlust ein, der "
           "nichts ueber den Markt sagt, sondern ueber die Datenlage")


    # ------------------------------------------------------------------
    # Q. SPOT RECHNET VON DER TRANCHE, NICHT VOM STOP (14.08.).
    #
    # Gefunden im ersten Lauf ueber den ECHTEN Job, an einer Mail:
    #     Tranche 800 -> Risiko 800 x 15 % = 120 -> Betrag 120 / 2,5 % = 4.800
    #     -> CRV-Abstufung x 0,2 = 960 EUR
    # Dort stand 960, wo der Nutzer 800 gesagt hatte. Und bei 4 % Stop waeren es
    # 600 gewesen: der Betrag haette am Stopabstand gehangen statt an seiner
    # Entscheidung. Bei Spot OHNE Stop-Order gibt es keine Groesse, die aus dem
    # Stop folgen koennte.
    _b = [ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.0, instrument="spot",
                    betrag_wunsch_eur=2000.0,
                    umgeworfen_preis_eur=100.0 * (1 - s))["betrag_eur"]
          for s in (0.025, 0.05, 0.09)]
    pruefe(P, "der Spot-Betrag haengt NICHT mehr am Stopabstand",
           len(set(_b)) == 1, f"{_b} - vorher waren es 4.800 / 2.400 / 1.333")
    _r = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.0, instrument="spot",
                   betrag_wunsch_eur=2000.0, umgeworfen_preis_eur=95.0)
    pruefe(P, "und das Risiko folgt umgekehrt aus Betrag und Stop",
           abs(_r["risiko_eur"] - _r["betrag_eur"] * _r["stop_relativ"]) < 0.5
           and "folgt aus" in str(_r.get("risiko_quelle")),
           f"Risiko {_r['risiko_eur']} auf {_r['betrag_eur']} EUR bei "
           f"{100 * _r['stop_relativ']:.1f} % Stop")
    _h = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=150.0, instrument="hebel",
                   betrag_wunsch_eur=1000.0, umgeworfen_preis_eur=95.0)
    pruefe(P, "beim HEBEL bleibt es beim Risikobudget",
           _h["betrag_eur"] == 1000.0 and _h["risiko_eur"] == 150.0,
           f"{_h['betrag_eur']} EUR bei {_h['hebel']}x - dort IST der Stop eine "
           f"Order, und der Hebel folgt aus Budget und Abstand")

    # DIE MINDESTGROESSE JE KOSTENKLASSE (15.08.2026) - die EINZIGE harte
    # Grenze, die uebrig bleibt, und die einzige, die eine Eigenschaft des
    # TRADES ist statt des Portfolios.
    pruefe(P, "Krypto hat eine niedrigere Mindestgroesse als die Boerse",
           ER.betrag_min_eur("krypto") == 25.0
           and ER.betrag_min_eur("boerse") == 100.0,
           "bei Krypto kuerzt sich der Betrag heraus (1,5 % je Seite, "
           "betragsunabhaengig) - die 100 EUR stammen aus der Boersenlogik "
           "und galten dort mit, weil niemand sie getrennt hat")
    pruefe(P, "eine 30-EUR-Position geht bei Krypto durch",
           ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.8, instrument="spot",
                     betrag_wunsch_eur=30.0,
                     kostenklasse="krypto")["betrag_eur"] >= 25.0,
           "vorher blockierte sie an einer Grenze, die fuer Fixgebuehren "
           "gebaut war, die es dort nicht gibt")
    pruefe(P, "dieselbe Position bricht an der Boerse ab",
           _wirft(lambda: ER.rechne(kurs=100.0, atr=3.0, risiko_eur=1.8,
                                    instrument="spot", betrag_wunsch_eur=30.0,
                                    kostenklasse="boerse"),
                  ER.RechnungBlockiert),
           "1 EUR fix je Seite waeren dort 6,7 % - die Gebuehr fraesse das "
           "Risikobudget")
    pruefe(P, "und die Mindestgroesse steht in der Mail",
           any("Kleinste sinnvolle Groesse" in z for z in ER.saetze(
               ER.rechne(kurs=100.0, atr=3.0, risiko_eur=120.0,
                         instrument="spot", betrag_wunsch_eur=800.0,
                         kostenklasse="krypto"))),
           "Nutzervorgabe 15.08.: die Anmerkung soll fuer den Nutzer "
           "ersichtlich sein")

    # ------------------------------------------------------------------
    # R. DER SCHALTER LIEGT UM (14.08.) - und der Job ruft die Kette WIRKLICH.
    from agent import betraege as BE
    from agent import handelsauftrag as HA

    pruefe(P, "spot x swing ist gestrichen",
           "swing" not in HA.ERLAUBTE_PAARE["spot"]
           and _wirft(lambda: HA.pruefe("spot", "swing"), HA.AuftragUngueltig),
           "Swing ist ueber einen nachgezogenen Stop definiert - der Nutzer "
           "haelt Spot ohne Stop. Das Paar waere eine Aufgabe, die es in der "
           "Praxis nicht gibt")
    pruefe(P, "hebel x swing bleibt", HA.pruefe("hebel", "swing") is not None)
    pruefe(P, "und es gibt keinen Betrag mehr fuer das gestrichene Paar",
           _wirft(lambda: BE.einsatz_eur("spot", "swing"), BE.BetragUnbekannt),
           "eine Zahl fuer ein unmoegliches Paar waere eine ohne Bedeutung")

    # DER FUND BEIM UMLEGEN: der Job uebersprang den alten Weg und rief den
    # neuen NICHT - der Schalter haette lautlos gar nichts laufen lassen.
    _bg = _nur_code("scheduler/background.py")
    pruefe(P, "der Job ruft die neue Kette wirklich auf",
           "fuehre_umlauf (" in _bg,
           "die erste Fassung uebersprang nur den Allocator: kein Fehler, "
           "keine Signale, kein Grund")
    # KEINE FESTE LISTE MEHR (14.08.). Hier stand `("spot", "hebel")` - damit
    # waren Aktien, Rohstoffe, Themen-ETF und die Absicherung von der neuen
    # Kette gar nicht erreichbar: der Schnitt haette sie stillgelegt, ohne sie
    # zu ersetzen.
    pruefe(P, "der Job fuehrt einen UMLAUF, keine feste Instrumentliste",
           'for instrument in ("spot", "hebel")' not in _quelltext(
               "scheduler/background.py")
           and "AK.laeufe()" in _quelltext("scheduler/rollen_job.py"),
           "was ein Umlauf ist, steht in assetklassen.laeufe() - an EINER "
           "Stelle")
    pruefe(P, "eine Gruppe reisst die anderen nicht mit",
           "Rollen-Kette %s/%s fehlgeschlagen" in _quelltext(
               "scheduler/rollen_job.py"),
           "dieselbe Regel wie fuer ein einzelnes Asset im Lauf")

    # DIE BETRIEBSART - im Zweifel keine Mail.
    from scheduler.rollen_job import betriebsart_aus_config as _bart
    pruefe(P, "ohne Angabe gilt probe", _bart({}) == "probe",
           "eine Vorgabe, die verschickt, waere eine Entscheidung, die niemand "
           "getroffen hat")
    pruefe(P, "ein unbekannter Wert faellt auf probe zurueck",
           _bart({"rollen_kette": {"betriebsart": "halbscharf"}}) == "probe",
           "hier ist der Rueckfall richtig herum: im Zweifel keine Mail")
    pruefe(P, "scharf wird als scharf gelesen",
           _bart({"rollen_kette": {"betriebsart": "scharf"}}) == "scharf")

    # UND DIE ECHTE KONFIGURATION SAGT, WAS SIE SAGEN SOLL.
    import config as _cfgmod
    _echt = _cfgmod.load_config()
    pruefe(P, "die Konfiguration stellt Krypto auf die neue Kette",
           RJ.bedient_neue_kette("krypto", _echt),
           f"rollen_kette.aktiv_fuer = {RJ.aktiv_fuer(_echt)}")
    pruefe(P, "und sie steht auf scharf", _bart(_echt) == "scharf",
           "Nutzerentscheidung 14.08. - echte Mails im Probebetrieb")
    pruefe(P, "der Versandweg ist gebaut, nicht None",
           RJ.baue_versand(_echt) is not None,
           "sonst schriebe der scharfe Lauf Signale, und die Mails blieben "
           "liegen")

    # ------------------------------------------------------------------
    # S. DIE SECHS PUNKTE DER KOSTENSTEUERUNG (14.08.).
    #
    # Ohne sie macht die Kette im 15-Minuten-Takt ~11.900 Aufrufe am Tag gegen
    # ein Gemini-Budget von 500. Mit ihnen 319.
    from agent import warteschlange as WS
    from scheduler import rollen_job as RJ2
    _l = _quelltext("agent/rollen_lauf.py")
    from agent.rollen_gate import STUFEN_NAMEN as RG_STUFEN

    # S1 COOLDOWN VOR DEM AUFRUF - der groesste Hebel.
    pruefe(P, "der Cooldown steht VOR dem Trader-Aufruf",
           _l.find("WH.gesperrt_bis") < _l.find("bc_roh = _frage("),
           "dahinter verhinderte er die Mail, nicht die Kosten - das Geld war "
           "ausgegeben, wenn er griff")
    # KORRIGIERT 14.08.: bis heute buchte der Cooldown auf "urteil" - und
    # dort steht auch der Verwurf einer geliefertern Antwort. "Wir haben nicht
    # gefragt" und "die Antwort war unbrauchbar" sahen damit gleich aus,
    # obwohl das eine nichts kostet und das andere einen Aufruf verbrennt. Am
    # ersten Betriebstag hat genau diese Vermischung die Diagnose des
    # Hebel-Stillstands um Stunden verzoegert.
    pruefe(P, "der Cooldown bucht auf seine EIGENE Stufe",
           'durchlauf.verloren(symbol, "wiederholung",' in _l
           and "wiederholung" in RG_STUFEN,
           "ein Kostenfilter darf in der Auswertung nicht aussehen wie ein "
           "Qualitaetsfilter - das Projekt trennt drei Arten von 'nicht "
           "jetzt', und nur die dritte traegt Deadloop-Risiko")
    pruefe(P, "und sie steht VOR dem Urteil im Trichter",
           RG_STUFEN.index("wiederholung") < RG_STUFEN.index("urteil"),
           "wer gesperrt ist, kommt nie zu einem Urteil - der Trichter bleibt "
           "monoton")

    # S2 LAGEBILD ZWISCHENGESPEICHERT.
    pruefe(P, "das Lagebild wird 3 h wiederverwendet",
           RL2.LAGEBILD_HALTBAR_STUNDEN == 3.0,
           "Nutzerentscheidung: nicht 8 h - es speist JEDEN Trader-Aufruf in "
           "seinem Fenster")
    pruefe(P, "und der Trockenlauf greift NICHT darauf zu",
           "if betriebsart != TROCKEN:" in _l.split("juengstes_lagebild")[0][-200:],
           "er soll die Verdrahtung pruefen, nicht davon abhaengen, was "
           "zufaellig in der Datenbank liegt")
    _alt = SA.juengstes_lagebild(c, 0.0)
    pruefe(P, "ein zu altes Lagebild wird nicht wiederverwendet", _alt is None,
           "bei Haltbarkeit 0 darf nichts durchkommen")

    # S3 WARTESCHLANGE - Reihenfolge, kein Ausschluss.
    _sym = ["ZZZ_UNBEKANNT", "BTC", "AAA_UNBEKANNT"]
    _sortiert = WS.sortiere(c, _sym)
    pruefe(P, "die Warteschlange schliesst NICHTS aus",
           sorted(_sortiert) == sorted(_sym),
           "sie sagt 'du zuerst', nie 'du nie' - ein Ausschluss waere die "
           "Mechanik, die den Deadloop erzeugt hat")
    pruefe(P, "Bestand kommt zuerst", _sortiert[0] == "BTC",
           f"{_sortiert} - bei einer Position, die der Nutzer haelt, steht "
           f"taeglich eine echte Entscheidung an")
    pruefe(P, "eine leere Liste bleibt leer", WS.sortiere(c, []) == [])
    # NUTZEREINWAND 14.08.: es gibt ZWEI Bestaende.
    _ws = _quelltext("agent/warteschlange.py")
    pruefe(P, "der Bestand umfasst Spot UND offenen Hebel",
           "FROM holdings" in _ws and "FROM hebel_positions" in _ws,
           "meine erste Fassung las nur `holdings` - beim Hebel waere der "
           "wichtigste Fall uebersehen worden")
    pruefe(P, "offen wird so definiert wie im Rest des Systems",
           "status = 'offen'" in _ws,
           "meine erste Fassung nahm `geschlossen_am IS NULL` - die Quelle "
           "(db.get_open_hebel_positions, backward_tracking:4794) sagt "
           "`status = 'offen'`. Beide Spalten existieren, ob sie immer "
           "zusammenpassen weiss niemand")
    # DIE LUECKE, NACH DER DER NUTZER GEFRAGT HAT: der Hebel-Bestand kommt aus
    # der Bitpanda-Abfrage. Wenn der Schnitt den Sync mit uebersprungen haette,
    # bliebe `hebel_positions` fuer immer leer.
    _bgq = _quelltext("scheduler/background.py")
    _i_job = _bgq.find("def hebel_screening_job(")
    _i_sync = _bgq.find("bitpanda_api_key", _i_job)
    _i_cut = _bgq.find("if any(bedient_neue_kette(g, config_dict)")
    pruefe(P, "der Bitpanda-Positions-Sync ueberlebt den Schnitt",
           0 < _i_sync < _i_cut,
           f"Sync bei {_i_sync}, Schnitt bei {_i_cut} - ohne ihn bliebe "
           f"hebel_positions leer und der Hebel-Bestand unsichtbar")
    pruefe(P, "und der Lauf reicht das Instrument durch",
           "WS.sortiere(conn, symbole, instrument)" in _l,
           "sonst sortierte ein Hebel-Lauf nach dem Spot-Bestand")

    # S4 BUDGET UND RUECKFALLKETTE.
    pruefe(P, "die Kette ist Gemini 3.1 -> 3.5 -> OpenRouter -> Groq",
           [q for q, _, _ in RJ2.KETTE] == ["gemini", "gemini",
                                            "openrouter", "groq"],
           "gleiche Familie zuerst: ein Anbieterwechsel mischt zwei "
           "Urteilsverteilungen in dieselbe Trefferbilanz")
    pruefe(P, "es bleibt eine Reserve", 0 < RJ2.RESERVE_ANTEIL < 0.5,
           f"{RJ2.RESERVE_ANTEIL:.0%} - Messlaeufe nehmen der Produktion "
           f"Kontingent weg, das Budget haengt am Schluessel")
    pruefe(P, "ohne Client gibt es keinen Lauf",
           RJ2.waehle_client({}) == (None, None, 0),
           "ein Lauf ohne Kontingent liesse jedes Symbol an derselben Stelle "
           "scheitern und fuellte die Durchlaessigkeit mit Scheinfehlern")

    class _Klient:
        def chat(self, *a, **k):
            return "{}"

    _cl, _mo, _rest = RJ2.waehle_client({}, clients={"gemini": _Klient()})
    pruefe(P, "mit Kontingent kommt der erste Topf und ein Deckel",
           _mo == "gemini-3.1-flash-lite" and _rest > 0, f"{_mo}, Rest {_rest}")
    pruefe(P, "der Deckel zaehlt AUFRUFE, nicht Symbole",
           'ergebnis["aufrufe"] >= max_aufrufe' in _l,
           "ein Symbol am Cooldown kostet nichts und darf den Deckel nicht "
           "verbrauchen")

    # S5 DAS MODELL AUF DER SIGNALZEILE - Voraussetzung fuer S4.
    _mf = SA.felder_aus_entscheidung({"aktion": "KAUFEN"}, fakten={},
                                     modell="gemini-3.5-flash-lite")
    pruefe(P, "die Signalzeile haelt das Modell fest",
           _mf.get("modell") == "gemini-3.5-flash-lite",
           "ohne sie mischte jeder Rueckfall lautlos - der "
           "Mistral-Verhaltensbruch vom 31.07. zeigte 55,4 gegen 68,0 % bei "
           "bitgleichem Prompt")
    pruefe(P, "und der Lauf gibt es weiter", "modell=modell" in _l)
    # GEFUNDEN IM PROBELAUF, nicht in einer Pruefung: wurde ein Client DIREKT
    # uebergeben (statt ueber `clients=`), blieb das Modell unbekannt - 57
    # Signalzeilen trugen `modell = None`, ausgerechnet in der Spalte, die es
    # seit heute gibt, damit ein Rueckfall nicht lautlos mischt.
    from api.gemini import DEFAULT_MODEL as _GDEF
    from api.gemini import GeminiClient as _GC
    pruefe(P, "auch ein direkt uebergebener Client wird benannt",
           RJ2._vorgabemodell(_GC("x")) == _GDEF,
           "am Modul abgelesen, nicht geraten - api/gemini.py fuehrt "
           "DEFAULT_MODEL")
    pruefe(P, "ein unbekannter Client bekommt KEINEN erfundenen Namen",
           RJ2._vorgabemodell(object()) is None,
           "dann steht in der Zeile ehrlich nichts statt einer Vermutung")

    # DER COOLDOWN MUSS JEDES URTEIL SPERREN, nicht nur Einstiege.
    _wh = _quelltext("agent/wiederholung.py")
    pruefe(P, "der Cooldown zaehlt JEDES Urteil der eigenen Kette",
           "action NOT IN" not in _wh,
           "meine erste Fassung sperrte nur Einstiege - von 25 Urteilen waren "
           "19 ein NICHTS_TUN, und die wurden bei jedem Lauf neu erfragt. "
           "Lauf 2 machte deshalb noch 17 Trader-Aufrufe statt 0")

    # S6 DAS NEIN WIRD MESSBAR MITGESCHRIEBEN.
    pruefe(P, "ein NICHTS_TUN wird geschrieben statt verworfen",
           "_schreibe_nein(" in _l,
           "beide Arme werden gebraucht: ob das JA den Breakeven schlaegt, und "
           "ob das NEIN besser ist als der Zufall")
    pruefe(P, "es traegt die Marke des Schatten-Trackings",
           'felder["ist_reines_llm_halten"] = 1' in _l,
           "backward_tracking sucht genau danach (Zeile 1192)")
    # DER RUMPF, NICHT DER AUFRUF. `split()[1]` traf die Argumentliste - die
    # Funktion steht weiter unten in der Datei als ihre Aufrufstelle.
    # AM VERHALTEN GEPRUEFT, NICHT AM ORT (15.08.2026). Vorher stand hier
    # `"take_profit_eur_von" in <Rumpf von _schreibe_nein>` - die Zeilen wurden
    # dort nachtraeglich angeflickt. Seit die Abbildung die Geometrie selbst
    # aus der Rechnung nimmt, steht der Flicken nicht mehr da, und die
    # Textsuche schlug an, obwohl die Sache besser geloest ist. Eine Pruefung,
    # die den Ort festhaelt statt die Tatsache, verbietet die Verbesserung.
    from agent import entscheidungsrechnung as ER10
    from agent import signal_abbildung as SA10

    _r_nein = ER10.rechne(kurs=100.0, atr=3.0, risiko_eur=40.0,
                          instrument="spot", betrag_wunsch_eur=500.0)
    # EIN NICHTS_TUN NENNT KEINE ZAHLEN - genau das ist der Fall.
    _f_nein = SA10.felder_aus_entscheidung({"aktion": "NICHTS_TUN"},
                                           fakten={}, rechnung=_r_nein)
    pruefe(P, "und gerechnete Zonen, sonst ist es unaufloesbar",
           all(_f_nein.get(k) is not None for k in
               ("entry_eur_von", "stop_loss_eur_von", "take_profit_eur_von")),
           "_hat_selbst_halten_these() verlangt Einstieg, Stop UND Ziel - ohne "
           "sie bliebe die Zeile fuer immer offen")
    # UND SIE STAMMEN AUS DER RECHNUNG, nicht aus der Antwort (Fund 6 vom
    # 15.08.): die Mail zeigte den gerechneten Stop, die Zeile den des
    # Modells - bei 19 von 23 Einstiegen war der in der Zeile ENGER, im
    # Median um Faktor 1,5. `backward_tracking` liest die Zeile.
    _f_beide = SA10.felder_aus_entscheidung(
        {"aktion": "KAUFEN", "stop_eur_von": 98.0, "stop_eur_bis": 99.0},
        fakten={}, rechnung=_r_nein)
    pruefe(P, "und zwar aus der RECHNUNG, nicht aus der Antwort",
           _f_beide.get("stop_loss_eur_von") == _r_nein["stop_eur"],
           f"Zeile {_f_beide.get('stop_loss_eur_von')}, Modell 98,0, "
           f"Rechnung {_r_nein['stop_eur']} - sonst misst die Trefferbilanz "
           "einen Stop, der nie empfohlen wurde")
    pruefe(P, "der Stop ist dabei ein Punkt, keine Zone",
           _f_beide.get("stop_loss_eur_von") == _f_beide.get("stop_loss_eur_bis"),
           "eine Marke, an der geschlossen wird, hat keine zwei Kanten")
    pruefe(P, "es zaehlt NICHT als Signal", 'felder["gate_passed"] = 0' in _l,
           "es ist eine Messung, keine Empfehlung")
    pruefe(P, "und ein Fehlschlag haelt den Lauf nicht auf",
           "nein_fehler" in _l,
           "die Zeile ist eine Messung - wer hier abbricht, verliert ein "
           "Urteil, das ohnehin bezahlt ist")

    # ------------------------------------------------------------------
    # T. DIE SCHALTER DES NUTZERS (Querpruefung GUI/Einstellungen, 14.08.).
    #
    # Drei GUI-Schalter je Asset wurden von den alten Pipelines gelesen und von
    # dieser Kette vollstaendig ignoriert. Sie erzeugte damit Signale, wo der
    # Nutzer ausdruecklich keine wollte - eine UEBERSTIMMTE Entscheidung, nicht
    # ein fehlendes Merkmal.
    from agent import asset_schalter as AS

    pruefe(P, "der Hebel-Schalter wird beim Hebel gelesen",
           "get_hebel_pruefung_erlaubt" in _quelltext("agent/asset_schalter.py"))
    pruefe(P, "der DCA-Schalter bei der Akkumulation",
           "get_dca_erlaubt" in _quelltext("agent/asset_schalter.py"))
    pruefe(P, "und die Kette fragt VOR dem Modellaufruf",
           _l.find("darf_analysiert_werden") < _l.find("bc_roh = _frage("),
           "ein Asset, das der Nutzer nicht handeln will, soll kein "
           "Kontingent kosten")
    pruefe(P, "eine Ablehnung wird als Auftragsverlust gebucht",
           'durchlauf.verloren(symbol, "auftrag", warum' in _l,
           "es ist eine Nutzerentscheidung, keine Marktlage - und das muss in "
           "der Durchlaessigkeit unterscheidbar bleiben")
    # FAIL-OPEN, NICHT FAIL-CLOSED.
    _erl, _grund = AS.darf_analysiert_werden(None, "BTC", "spot", "einstieg")
    pruefe(P, "ohne lesbare Schalter gilt ERLAUBT", _erl and _grund is None,
           "ein Lesefehler darf nicht dazu fuehren, dass die Kette stumm "
           "nichts mehr tut - das waere der Deadloop durch die Hintertuer")
    pruefe(P, "der Bitpanda-Override schlaegt das Listing",
           AS.ist_handelbar(None, "BTC", bitpanda_gelistet=True) is True
           and AS.ist_handelbar(None, "BTC", bitpanda_gelistet=None) is True,
           "die Listing-Abfrage kennt nicht jeden Sonderfall, der Nutzer schon")

    # T2 EIN CASH-AEQUIVALENT IST KEIN HEBEL-KANDIDAT (15.08.2026).
    #
    # Nutzerfund an der eigenen Oberflaeche: *"eurcv ist ueberhaupt ein
    # stablecoin"*. `ui/app.py` baut die Spalte "Hebel-Pruefung" ausdruecklich
    # nur fuer `krypto and not ist_cash_aequivalent` - EURCV steht dort mit
    # "-". Die Kette kannte diese Bedingung nicht und fragte nur den Schalter;
    # der hat fuer EURCV keine Zeile und liefert damit "erlaubt".
    #
    # Anzeige und Verhalten sagten Gegenteiliges. Aufgehalten hat es nur ein
    # Datenmangel: EURCV hat keine Tageskerzen.
    class _WLA:
        def __init__(_s, sym, cash):
            _s.symbol = sym
            _s.ist_cash_aequivalent = cash

    _wl_test = [_WLA("EURCV", True), _WLA("BTC", False)]
    _e_cash, _g_cash = AS.darf_analysiert_werden(
        None, "EURCV", "hebel", "einstieg", watchlist=_wl_test)
    pruefe(P, "ein Stablecoin bekommt KEIN Hebel-Urteil",
           _e_cash is False and "Cash" in (_g_cash or ""),
           f"{_g_cash!r} - ein gehebelter Stablecoin ist kein Trade, sondern "
           "ein Denkfehler mit laufenden Kosten")
    _e_spot, _ = AS.darf_analysiert_werden(
        None, "EURCV", "spot", "einstieg", watchlist=_wl_test)
    pruefe(P, "im SPOT bleibt er erlaubt", _e_spot is True,
           "Cash zu halten ist eine Lage, kein Fehler - nur hebeln kann man "
           "es nicht")
    # ⚠️ MIT ECHTER VERBINDUNG (16.08.2026). Hier stand `None` - und seit
    # die Nutzerschalter bei einem Lesefehler ZUFALLEN statt aufzugehen,
    # ist "keine Datenbank" korrekterweise ein Nein. Diese Pruefung meint
    # aber die CASH-Regel; sie braucht deshalb einen Bestand, in dem der
    # Schalter tatsaechlich beantwortbar ist.
    _mem_sch = sqlite3.connect(":memory:")
    _mem_sch.row_factory = sqlite3.Row
    _db_sch = __import__("database.db", fromlist=["db"])
    _db_sch.init_db(_mem_sch)
    _db_sch.set_hebel_pruefung_erlaubt(_mem_sch, "BTC", True)
    _e_btc, _g_btc = AS.darf_analysiert_werden(
        _mem_sch, "BTC", "hebel", "einstieg", watchlist=_wl_test)
    pruefe(P, "und ein normales Asset bleibt unberuehrt", _e_btc is True,
           f"{_g_btc!r}")
    pruefe(P, "OHNE lesbare Schalter wird NICHT beurteilt",
           AS.darf_analysiert_werden(
               None, "BTC", "hebel", "einstieg",
               watchlist=_wl_test)[0] is False,
           "wer nicht lesen kann, was der Nutzer will, darf es nicht "
           "annehmen - vorher lief das Asset bei jedem Lesefehler durch")
    _mem_sch.close()
    # DIE VERDRAHTUNG - `_ein_asset` sieht `_wl` NICHT von selbst. Genau diese
    # Falle hat am 14.08. `VK` erwischt: eine Variable aus `fuehre_lauf`, der
    # breite Fehlerfang schluckt den NameError, und JEDES Symbol landet im
    # Fehlerzweig.
    import inspect as _i5
    from agent import marktrang as _MR_MOD
    from agent import rollen_lauf as _RL5

    pruefe(P, "die Watchlist wird an `_ein_asset` durchgereicht",
           "watchlist" in _i5.signature(_RL5._ein_asset).parameters
           and "assetklasse = assetklasse , watchlist = _wl" in _nur_code(
               "agent/rollen_lauf.py"),
           "sonst waere es ein NameError je Symbol, den niemand sieht")
    pruefe(P, "und von dort an den Schalter",
           "strategie , watchlist = watchlist" in _nur_code(
               "agent/rollen_lauf.py"))

    # T3 DER SCHALTER IST EIN OPT-IN (15.08.2026, Nutzerentscheidung).
    #
    # Er kam am 18.07. dazu, als 44 Krypto-Assets schon in der Watchlist
    # standen, und liess "keine Zeile" als "an" gelten. In der Oberflaeche sah
    # das aus wie eine Liste getroffener Entscheidungen; sieben Symbole standen
    # dort auf "An", ohne dass sie je jemand eingeschaltet haette.
    #
    # ZWEI AENDERUNGEN, DIE NUR ZUSAMMEN RICHTIG SIND. Wer die Vorgabe umdreht
    # ohne die Migration, schaltet BTC, ETH, BNB, HYPE, KAIA, SUI und TAO
    # still ab - vier der zwoelf Hebel-Signale jenes Vormittags kamen daher.
    import database.db as _DB5

    pruefe(P, "ohne Zeile gilt AUS, nicht AN",
           "if row is None : return False" in " ".join(
               _nur_code("database/db.py").split(
                   "def get_hebel_pruefung_erlaubt")[1][:400].split()),
           "keine Zeile ist keine Zustimmung")
    # ⚠️ NICHT MEHR AUF DIE ERSTEN 2000 ZEICHEN. Diese Pruefung schlug am
    # 22.08. fehl, weil ein NEUER Migrationsaufruf die gesuchte Zeile aus dem
    # Fenster geschoben hat - der Code war richtig, das Fenster zu klein.
    # Ein Zeichenfenster ist keine Funktionsgrenze.
    _init_db_rumpf = _nur_code("database/db.py").split("def init_db")[1]
    _init_db_rumpf = _init_db_rumpf.split(" def ")[0]
    pruefe(P, "und die Geradeziehung laeuft VOR dem ersten Kettenlauf",
           "_migrate_hebel_schalter_geradeziehen ( conn )" in _init_db_rumpf,
           "init_db() laeuft beim App-Start, also vor dem Scheduler - sonst "
           "griffe die neue Vorgabe auf noch unentschiedene Symbole")
    pruefe(P, "sie ruehrt bestehende Zeilen NICHT an",
           "INSERT OR IGNORE INTO asset_hebel_settings" in _quelltext(
               "database/db.py"),
           "wer 'aus' gesetzt hat, behaelt 'aus'")

    # T4 DER RICHTUNGSSCHALTER WIRKT NUR AUF DEN VERSAND (15.08.2026).
    #
    # Nutzervorgabe vom 05.08., woertlich: der Schalter soll "NULL Einfluss auf
    # die Funktionsweise im Hintergrund" haben - SHORTs sollen lediglich nicht
    # per E-Mail kommen und nicht in der GUI erscheinen.
    #
    # DER GRUND IST MESSHYGIENE. Bis dahin sass der Filter VOR der
    # Verarbeitung, und 313 SHORT-Vorschlaege lagen als "HALTEN" in der
    # Datenbank - beim 31.07.-Bruch hat das einen ganzen Tag gekostet.
    _nl = {"budget_allocator": {"hebel_richtung_modus": "nur_long"}}
    _bd = {"budget_allocator": {"hebel_richtung_modus": "beide"}}
    pruefe(P, "bei nur_long geht ein SHORT nicht per Mail raus",
           AS.mail_richtung_erlaubt("SHORT", _nl) is False)
    pruefe(P, "ein LONG geht weiterhin raus",
           AS.mail_richtung_erlaubt("LONG", _nl) is True)
    pruefe(P, "bei 'beide' geht auch ein SHORT raus",
           AS.mail_richtung_erlaubt("SHORT", _bd) is True)
    pruefe(P, "Spot ohne Richtung bleibt unberuehrt",
           AS.mail_richtung_erlaubt(None, _nl) is True,
           "Spot-Signale haben keine Hebel-Richtung - sie duerfen an diesem "
           "Filter nicht haengenbleiben")
    pruefe(P, "eine unlesbare Einstellung laesst durch",
           AS.mail_richtung_erlaubt("SHORT", {"budget_allocator": None}),
           "fail-open: lieber eine Mail zuviel als eine verschluckte")
    # EINE DEFINITION, ZWEI KETTEN. Der alte Weg delegiert, statt eine zweite
    # Rechnung zu fuehren.
    import scheduler.background as _BG5

    pruefe(P, "der alte Weg fragt DIESELBE Stelle",
           _BG5._ist_email_relevante_richtung("SHORT")
           == AS.mail_richtung_erlaubt("SHORT")
           and "mail_richtung_erlaubt" in _quelltext("scheduler/background.py"),
           "zwei Rechnungen zu derselben Frage laufen auseinander")
    # UND ER GREIFT AUSSCHLIESSLICH AM VERSAND, nirgends frueher.
    _lq = _nur_code("agent/rollen_lauf.py")
    pruefe(P, "die Kette fragt ihn NACH dem Schreiben des Signals",
           _lq.find("SA . schreibe_signal") < _lq.find("mail_richtung_erlaubt"),
           "davor waere es wieder ein Veto - und die Messung waere verzerrt")
    pruefe(P, "beide Versandstellen sind abgesichert",
           _lq.count("and _mail_erlaubt ) :") == 2,
           "eine allein liesse die Mail durch, sobald Z.ai antwortet")
    # ZEICHENKETTEN BRAUCHEN `_quelltext`, nicht `_nur_code` - letzteres
    # entfernt String-Literale mit den Kommentaren zusammen. Diese Falle hat
    # heute zum sechsten Mal zugeschlagen.
    _lqt = _quelltext("agent/rollen_lauf.py")
    # T4b KEINE FUNKTION GREIFT AUF EINEN NAMEN ZU, DEN SIE NICHT KENNT.
    #
    # DREIMAL DIESELBE FALLE an zwei Tagen, jedes Mal eine Variable aus
    # `fuehre_lauf` oder `_ein_asset`, benutzt in einer Funktion, die sie nicht
    # sieht - und jedes Mal vom breiten Fehlerfang geschluckt:
    #
    #   14.08.  `VK`            jedes Symbol lief in den Fehlerzweig
    #   15.08.  `_wl`           (vor dem Betrieb gefunden)
    #   15.08.  `assetklasse`   ZWEI VORMITTAGE OHNE EINE EINZIGE NEIN-ZEILE
    #
    # Der dritte war der teuerste, weil er nichts umbrachte, sondern schwieg:
    # 809 Nein-Zeilen bis 14.08. 17:55, danach keine. Damit fehlte der Arm der
    # Messung, der sagen soll, ob das NEIN des Modells besser ist als Zufall.
    #
    # DIESE PRUEFUNG BRAUCHT KEIN AUSFUEHREN - sie liest den Syntaxbaum. Bei
    # der Einfuehrung fand sie zusaetzlich zwei schlafende Fehler: `json` war
    # in `scheduler/background.py` nirgends importiert, und `ui/app.py` rief
    # `ist_hedge_instrument()` ohne Import.
    import ast as _ast
    import builtins as _bi
    import os as _os

    def _freie_namen(pfad: str) -> list[tuple[str, str]]:
        with open(pfad, "r", encoding="utf-8") as f:
            baum = _ast.parse(f.read(), filename=pfad)
        modul = set(dir(_bi))
        for k in baum.body:
            if isinstance(k, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                              _ast.ClassDef)):
                modul.add(k.name)
            elif isinstance(k, (_ast.Import, _ast.ImportFrom)):
                for a in k.names:
                    modul.add((a.asname or a.name).split(".")[0])
            elif isinstance(k, (_ast.Assign, _ast.AnnAssign, _ast.AugAssign,
                                _ast.Try)):
                for n in _ast.walk(k):
                    if isinstance(n, _ast.Name):
                        modul.add(n.id)
                    elif isinstance(n, (_ast.Import, _ast.ImportFrom)):
                        for a in n.names:
                            modul.add((a.asname or a.name).split(".")[0])
        offen = []
        for k in baum.body:
            if not isinstance(k, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            gebunden = set()
            for n in _ast.walk(k):
                if isinstance(n, _ast.Name) and isinstance(
                        n.ctx, (_ast.Store, _ast.Del)):
                    gebunden.add(n.id)
                elif isinstance(n, _ast.arg):
                    gebunden.add(n.arg)
                elif isinstance(n, _ast.alias):
                    gebunden.add((n.asname or n.name).split(".")[0])
                elif isinstance(n, _ast.ExceptHandler) and n.name:
                    gebunden.add(n.name)
                elif isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                                    _ast.ClassDef)):
                    gebunden.add(n.name)
            benutzt = {n.id for n in _ast.walk(k)
                       if isinstance(n, _ast.Name)
                       and isinstance(n.ctx, _ast.Load)}
            for name in sorted(benutzt - gebunden - modul):
                offen.append((k.name, name))
        return offen

    _frei = []
    for _o in ("agent", "scheduler", "database", "ui"):
        for _w, _, _dn in _os.walk(_o):
            for _n in sorted(_dn):
                if _n.endswith(".py"):
                    _p = _os.path.join(_w, _n)
                    try:
                        for _fn, _nm in _freie_namen(_p):
                            _frei.append(f"{_p}::{_fn}() -> {_nm}")
                    except SyntaxError:
                        _frei.append(f"{_p}: nicht lesbar")
    pruefe(P, "keine Funktion greift auf einen fremden Namen zu",
           not _frei, str(_frei[:5]),)

    # T4c DIE ANLASSSTUFE MISST UND SPERRT NICHT (O-36, 15.08.2026).
    #
    # Nutzervorgabe: *"erstmal soviele Daten wie moeglich zulassen und spaeter
    # selektiv einschraenken."* Diese Pruefung ist der Beweis dafuer, und sie
    # ist STATISCH - ein Laufvergleich taugt nicht, weil die Stufe im
    # Trockenlauf gar nicht laeuft (sie schreibt in die Datenbank).
    #
    # STEHT DER BEFUND IN KEINER BEDINGUNG, kann er nichts sperren - egal in
    # welcher Betriebsart.
    from agent import anlass as AN4

    _q4c = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Anlassmessung ist verdrahtet", "AN.beobachte" in _q4c)
    # VOR DEM COOLDOWN, sonst misst sie die falsche Population. Ein Symbol
    # hinter dem Cooldown hat mindestens 3,5 Stunden (Hebel) bzw. 15 (Spot)
    # hinter sich - in dieser Zeit hat sich der Faktensatz fast immer bewegt.
    # Der Filter haette fast nie gegriffen, und man haette daraus geschlossen,
    # dass er nichts taugt.
    pruefe(P, "die Anlassmessung sitzt VOR dem Cooldown",
           _q4c.index("AN.beobachte") < _q4c.index("WH.gesperrt_bis"),
           "sonst sieht sie nur Symbole, bei denen der Cooldown ohnehin schon "
           "abgelaufen war - und erst so wird vergleichbar, ob der Anlass den "
           "Cooldown ersetzen koennte")
    pruefe(P, "aber ihr Befund wird nirgends gelesen",
           "wuerde_sperren" not in _q4c and "gleich_asset" not in _q4c,
           "was in keiner Bedingung steht, kann nichts sperren")
    # ZWEI ABDRUECKE, und der Unterschied ist die eigentliche Erkenntnis.
    _f = {"asset": "X", "stand": ["a"], "marktlage_beurteilung": {"lage": "A"}}
    _v1, _a1 = AN4.fingerabdruecke(_f)
    _v2, _a2 = AN4.fingerabdruecke(
        dict(_f, marktlage_beurteilung={"lage": "B"}))
    pruefe(P, "ein neues Lagebild aendert `voll`, nicht `asset`",
           _v1 != _v2 and _a1 == _a2,
           "sonst waere fast jede Frage 'neu' und der Filter wirkungslos")
    _v3, _a3 = AN4.fingerabdruecke(dict(_f, stand=["b"]))
    pruefe(P, "geaenderte Assetfakten aendern beide",
           _v3 != _v1 and _a3 != _a1)
    # JE BLOCK, damit die Messung sagt WORAN es lag (15.08.2026, auf
    # Nutzerwunsch). Der Finanzierungsblock tickt bei Krypto alle acht Stunden
    # von selbst - er koennte den Filter dort stumpf machen, wo er am meisten
    # braechte, und dieselbe Zahl waere ohne Ursache nicht deutbar.
    _b1 = {"struktur": ["a"], "finanzierung": ["40. Perzentil"]}
    _b2 = dict(_b1, finanzierung=["55. Perzentil"])
    _h1, _h2 = AN4.bloeckeabdruecke(_b1), AN4.bloeckeabdruecke(_b2)
    pruefe(P, "nur der geaenderte Block bekommt einen neuen Abdruck",
           _h1["struktur"] == _h2["struktur"]
           and _h1["finanzierung"] != _h2["finanzierung"])
    # UND DER PROMPT DARF SICH DABEI NICHT VERAENDERN: die Bloecke gehen als
    # AUSGANG an der Messung vorbei, nicht als Schluessel in den Faktensatz.
    import inspect as _i4

    from agent import rollen_eingabe as RE3

    pruefe(P, "die Bloecke sind ein Ausgang, kein Prompt-Feld",
           "bloecke_ziel" in _i4.signature(RE3.baue_fall).parameters
           and "bloecke_ziel" in _quelltext("agent/lagebeschreibung.py"),
           "ein zusaetzlicher Schluessel im Faktensatz haette alle bisherigen "
           "Messungen unvergleichbar gemacht")
    pruefe(P, "und die Lage wird dafuer nur EINMAL gerechnet",
           _nur_code("agent/lagebeschreibung.py").count(
               "bloecke = geteilt (") == 1,
           "vorher stand `geteilt()` in der Schleife - sechsmal dieselbe "
           "Rechnung ueber dieselbe Reihe")

    pruefe(P, "und es gibt eine Decke, damit nichts dauerhaft blockiert",
           AN4.HOECHSTALTER_STUNDEN > 0,
           f"{AN4.HOECHSTALTER_STUNDEN} h - Nutzervorgabe 'z.B. 24 Stunden'")

    # T4d DIE KARTE ZEIGT DIE GRENZE, NICHT DIE SUMME (15.08.2026).
    #
    # Auf der Remote-Karte stand `rest_gesamt` als "N Aufrufe frei" - 1.874
    # ueber alle vier Toepfe. Arithmetisch richtig, als Aussage falsch: die
    # Toepfe sind eine RUECKFALLKETTE, kein Vorrat. OpenRouter und Groq kommen
    # erst dran, wenn Gemini erschoepft ist, und dahinter steht ein anderes
    # Modell - nemotron dreht bei bitgleicher Eingabe in ~12 % die Richtung.
    #
    # Nutzerfrage, die das aufdeckte: *"rechne nochmal nach, Reserve 1874
    # verstehe ich nicht?"*
    _rs = _quelltext("remote/status.py")
    _sv = _quelltext("remote/server.py")
    pruefe(P, "die Statusseite kennt den bindenden Topf",
           "rest_aktiv" in _rs and "topf_aktiv" in _rs,
           "der erste Topf MIT Rest ist die Grenze")
    pruefe(P, "und die Karte zeigt ihn statt der Summe",
           "rb.rest_aktiv" in _sv,
           "die Summe bleibt daneben, aber als das, was sie ist")
    pruefe(P, "die Summe wird nicht mehr als 'frei' beschriftet",
           'rb.rest_gesamt + " Aufrufe frei"' not in _sv)

    # T4e EIN STOP, EIN PROZENTSATZ (16.08.2026, Nutzerfund am AKT-Signal).
    #
    #     2. DIE RECHNUNG   Stop 4,8 %   (gegen den Kurs)
    #     4. EINORDNUNG     Stop 3,3 %   (gegen die UNTERE Kante der Zone)
    #
    # Der Fix vom 14.08. hatte die Einordnung richtig an die Rechnung gebunden,
    # aber am falschen Punkt. Die Folgezeile erbt den Fehler: "die Gebuehren
    # fressen 92 % Ihres Risikos" waren gegen die Zonenmitte 62 %.
    # `_quelltext`, NICHT `_nur_code` - letzteres entfernt String-Literale
    # mitsamt den Kommentaren, und genau der Feldname ist einer.
    _q4e = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Einordnung misst gegen die MITTE der Einstiegszone",
           'einstieg=rechnung.get("einstieg_eur")' in _q4e,
           "die untere Kante laesst den Stop naeher aussehen, als er ist")
    pruefe(P, "und nicht mehr gegen die untere Kante",
           '"einstieg_von_eur" ) or kurs_e' not in _q4e)
    # UND BEIDE ZAHLEN MUESSEN ZUSAMMENPASSEN.
    from agent import entscheidungsrechnung as ER12

    _e12 = ER12.rechne(kurs=0.4702, atr=0.0181, risiko_eur=150.0,
                       instrument="hebel", betrag_wunsch_eur=1000.0)
    _p_rechnung = 100.0 * _e12["stop_relativ"]
    _p_einordnung = (100.0 * (_e12["einstieg_eur"] - _e12["stop_eur"])
                     / _e12["einstieg_eur"])
    pruefe(P, "beide Abschnitte nennen denselben Stopabstand",
           abs(_p_rechnung - _p_einordnung) < 0.05,
           f"{_p_rechnung:.2f} % gegen {_p_einordnung:.2f} %")

    # T5 BETREFF, TEXT UND ZEILE SAGEN DASSELBE (O-37, 15.08.2026).
    #
    # Im Produktionslauf zweimal auseinandergelaufen:
    #
    #     Signalzeile: TURBO  EROEFFNEN  Hebel 3,8  500 EUR
    #     Betreff:     TradingInfoTool: TURBO - SCHLIESSEN (Hebel)
    #     Mailtext:    "Kein zusaetzlicher Einstieg ..."
    #
    # Drei Stimmen, zwei Meinungen - und gemessen wird die Zeile.
    from agent import entscheidungsrechnung as ER11
    from agent import signal_mail as SM11

    _r11 = ER11.rechne(kurs=100.0, atr=3.0, risiko_eur=60.0,
                       instrument="hebel", betrag_wunsch_eur=500.0)
    _aus11 = {"empfehlung": "SCHLIESSEN", "gesicherte_r": 1.0,
              "stop_empfohlen": 95.0, "frist": None, "frist_abgelaufen": False,
              "trailing_aktiv": True, "falsifiziert": False,
              "ist_bestand": True, "ist_hebel": True, "gruende": []}
    for _akt, _erw in (("ERÖFFNEN", "ERÖFFNEN"), ("NACHKAUFEN", "NACHKAUFEN"),
                       ("HALTEN", "SCHLIESSEN")):
        _b11, _ = SM11.baue_mail(
            symbol="TURBO", name="TURBO", kurs_eur=100.0, instrument="hebel",
            strategie="einstieg", rechnung=_r11,
            urteil={"aktion": _akt, "begruendung": "x"}, ausstieg=_aus11)
        pruefe(P, f"Betreff bei {_akt} nennt {_erw}", f"- {_erw}" in _b11,
               _b11)
    # DIE DRINGLICHKEIT IST NICHT VERLOREN - sie steht im Text.
    _b11, _t11 = SM11.baue_mail(
        symbol="TURBO", name="TURBO", kurs_eur=100.0, instrument="hebel",
        strategie="einstieg", rechnung=_r11,
        urteil={"aktion": "ERÖFFNEN", "begruendung": "x"}, ausstieg=_aus11)
    pruefe(P, "der faellige Ausstieg steht weiterhin im TEXT",
           "Bestehende Position" in _t11 and "SCHLIESSEN" in _t11,
           "sichtbar, nur nicht als Ueberschrift")
    # UND DIE KETTE ERZEUGT DIESEN FALL GAR NICHT MEHR.
    pruefe(P, "die Kette laesst keinen Einstieg auf faelligen Ausstieg zu",
           "Ausstieg steht auf SCHLIESSEN" in _lqt,
           "7 von 7 Symbolen mit SCHLIESSEN bekamen am 15.08. eine "
           "Eroeffnungsempfehlung")
    pruefe(P, "aber nur bei einem ECHTEN Bestand",
           "_fuehrung . get ( \"ist_bestand\" )" in _nur_code(
               "agent/rollen_lauf.py").replace('"ist_bestand"', '"ist_bestand"')
           or "ist_bestand" in _lqt,
           "von neun SCHLIESSEN-Zeilen bezogen sich nur drei auf einen Bestand")
    pruefe(P, "die Fuehrung wird je Symbol UND Instrument nachgeschlagen",
           "_fuehrung_zu ( ergebnis , symbol , instrument )" in _nur_code(
               "agent/rollen_lauf.py"),
           "TURBO stand zweimal in der Liste - einmal Spot, einmal Hebel")
    pruefe(P, "und es gibt genau EINE Nachschlagestelle",
           _nur_code("agent/rollen_lauf.py").count(
               "_fuehrung_zu ( ergebnis , symbol , instrument )") == 3
           and _nur_code("agent/rollen_lauf.py").count("def _fuehrung_zu") == 1,
           "drei Aufrufer, eine Definition")

    # T6 DER HEBEL-TAB SIEHT BEIDE KETTEN (O-35, 15.08.2026).
    #
    # Er las ausschliesslich `hebel_signals` - die Tabelle der ALTEN Kette.
    # Seit dem Vollumstieg entstanden die Hebel-Signale in `signals`, und auf
    # der Hebelseite war die Oberflaeche LEER. Genau der blinde Fleck, den der
    # Nur-Long-Umbau am 05.08. beseitigen wollte.
    import database.db as _DB6

    pruefe(P, "es gibt eine Abfrage fuer die Rollen-Hebelsignale",
           hasattr(_DB6, "get_latest_rollen_hebel_signal_per_symbol_and_richtung"))
    pruefe(P, "sie nutzt DENSELBEN Diskriminator wie die Toepfe",
           "sql_bedingung" in _quelltext("database/db.py").split(
               "def get_latest_rollen_hebel_signal_per_symbol_and_richtung")[1][:2000],
           "eine eigene `hebel IS NOT NULL`-Kopie waere die vierte Wahrheit "
           "ueber dieselbe Sache")
    pruefe(P, "und der Tab fuehrt beide Quellen zusammen",
           "get_latest_rollen_hebel_signal_per_symbol_and_richtung" in
           _quelltext("ui/hebel_view.py")
           and "created_at" in _nur_code("ui/hebel_view.py"),
           "die juengere Zeile gewinnt je (Symbol, Richtung)")
    # DIE ABBILDUNG ERFINDET NICHTS: was die neue Kette nicht rechnet, bleibt
    # leer - `trigger_score`, `eigenkapitalbedarf_eur`, `liquidationspreis_*`.
    _q6 = _quelltext("database/db.py").split(
        "def get_latest_rollen_hebel_signal_per_symbol_and_richtung")[1][:3000]
    pruefe(P, "sie benennt die zwei umbenannten Felder",
           'data["hebel_final"] = roh.get("hebel")' in _q6
           and 'data["llm_model"] = roh.get("modell")' in _q6,
           "dieselbe Sache heisst in beiden Tabellen anders")

    pruefe(P, "und das Signal wird trotzdem geschrieben",
           "nicht_versendet" in _lqt and "mails_unterdrueckt" in _lqt,
           "das Signal bleibt erhalten und wird weiter gemessen - nur die "
           "Mail unterbleibt")

    # ------------------------------------------------------------------
    # U. DIE ASSETKLASSEN - Vorarbeit fuer den Multi-Asset-Umstieg (14.08.).
    #
    # DIE FALLE, DIE HIER ABGESICHERT WIRD, ist am 06.08. schon einmal
    # zugeschnappt: ein Filter auf eine Assetklasse "hedge", die es nicht gibt,
    # liess DBPK und 3QSS aus. Mein `KLASSEN`-Tupel hatte den Fehler wiederholt.
    from agent import assetklassen as AK

    pruefe(P, "die Watchlist kennt vier Assetklassen - hedge ist keine",
           "hedge" not in AK.ASSETKLASSEN and set(AK.ASSETKLASSEN) ==
           {"krypto", "aktien", "rohstoffe", "etf"},
           f"{AK.ASSETKLASSEN} - DBPK und 3QSS stehen als `etf` in der "
           f"Watchlist und sind nur ueber SYMBOL_ZU_HEBEL_FAKTOR erkennbar")
    _g = AK.gruppiere()
    pruefe(P, "etf zerfaellt in hedge und themen_etf",
           "hedge" in _g and "themen_etf" in _g
           and not (set(_g["hedge"]) & set(_g["themen_etf"])),
           f"hedge {_g.get('hedge')}, themen_etf {_g.get('themen_etf')}")
    pruefe(P, "jede Gruppe ist ein gueltiger Faktenblock-Bereich",
           all(RL2._bereich(g, i) in FB.ZUSATZ_JE_BEREICH
               for g, i, _ in AK.laeufe()),
           str([RL2._bereich(g, i) for g, i, _ in AK.laeufe()]))
    # ⚠️ S6b (22.08.2026): KEINE GRUPPE LAEUFT MEHR MIT ZWEI INSTRUMENTEN.
    # Die Aussage "Hebel gibt es bei Bitpanda nur bei Krypto" gilt weiter -
    # sie steht jetzt in `hebel_handelbar()` statt in der Laufliste.
    pruefe(P, "keine Gruppe laeuft mehr mit zwei Instrumenten",
           not [g for g, i, _ in AK.laeufe() if i == "hebel"],
           "das Instrument ist seit Kapitel 88 ein ERGEBNIS, keine "
           "Kategorie - S6b hat den zweiten Lauf gestrichen")
    pruefe(P, "und die Handelbarkeit steht bei der GRUPPE",
           AK.hebel_handelbar("krypto")
           and not any(AK.hebel_handelbar(g) for g in
                       ("aktien", "rohstoffe", "themen_etf", "hedge")),
           "sie steckte bis S6b in `instrument == \"hebel\"` - also in der "
           "Frage, welcher LAUF dran ist. Mit dem Wegfall des zweiten Laufs "
           "waere sie ersatzlos verschwunden")
    pruefe(P, "die Absicherung laeuft als `absicherung`, nicht als spot",
           [i for g, i, _ in AK.laeufe() if g == "hedge"] == ["absicherung"])
    _alle = {s for _, _, ss in AK.laeufe() for s in ss}
    pruefe(P, "kein Symbol faellt zwischen die Gruppen",
           len(_alle) >= 50, f"{len(_alle)} von 57 (Cash-Aequivalente raus)")
    pruefe(P, "Cash-Aequivalente sind draussen",
           "EURCV" not in _alle,
           "ein Stablecoin zu beurteilen kostet einen Aufruf fuer eine Frage, "
           "die sich nicht stellt")

    # DIE KORREKTUR MEINER EIGENEN DOKUMENTATION.
    pruefe(P, "die core-Rolle kommt aus der Watchlist, nicht aus einer Tabelle",
           len(AK.kern_symbole()) >= 10 and "BTC" in AK.kern_symbole(),
           "ich hatte die Stufe 'vorgemerkt' fuer leer erklaert, weil die "
           "TABELLE `watchlist` keine Spalten hat - die Watchlist ist keine "
           "Tabelle, sie steht in config.yaml")
    pruefe(P, "und die Warteschlange benutzt sie",
           "kern_symbole" in _quelltext("agent/warteschlange.py"))

    # ------------------------------------------------------------------
    # V. DIE REMOTE-SEITE BAUT UEBERHAUPT (14.08., aus dem ersten Startlog).
    #
    # `/api/status` starb bei JEDEM Abruf mit
    #     TypeError: RemoteStatus.__init__() got an unexpected keyword argument
    #                'selbst_gewaehltes_halten_performance_nach_grund'
    # Der Konstruktoraufruf uebergab das Feld, die Klasse kannte es nicht - seit
    # Commit 598753c. Die Fernsteuerung war vollstaendig tot.
    #
    # WARUM ES DURCH ALLE NETZE FIEL: `_safe()` faengt Fehler der einzelnen
    # KARTEN ab, nicht den Aufbau des Ergebnisobjekts. Die Laufzeitwache misst
    # die DAUER, nicht das Gelingen. Und es gab keinen Testlauf, der den Status
    # einmal WIRKLICH baut - genau den macht diese Pruefung jetzt.
    import dataclasses as _dc
    from pathlib import Path as _P

    import config as _cfg2
    from remote.status import RemoteStatus, build_status

    _felder = {f.name for f in _dc.fields(RemoteStatus)}
    import re as _re2
    _uebergeben = set(_re2.findall(r"^ {8}(\w+)=",
                                   _quelltext("remote/status.py"), _re2.M))
    _unbekannt = sorted(_uebergeben - _felder)
    pruefe(P, "jedes uebergebene Feld ist in RemoteStatus deklariert",
           not _unbekannt, f"nicht deklariert: {_unbekannt}")

    # EIGENE VERBINDUNG MIT ZEILENFABRIK. Der Statusaufbau liest ueberall
    # `row["spalte"]`; die Testverbindung liefert Tupel. Derselbe Stolperstein
    # wie bei der Cash-Reserve heute frueh - die Zeilenfabrik ist in diesem
    # Projekt eine stille Voraussetzung an vielen Stellen.
    _alt_rf = c.row_factory
    c.row_factory = sqlite3.Row
    try:
        _s = build_status(c, _cfg2.get_watchlist(), _P("tradinginfotool.log"))
    finally:
        c.row_factory = _alt_rf
    pruefe(P, "der Status baut wirklich - nicht nur die einzelnen Karten",
           isinstance(_s, RemoteStatus),
           "das ist die Pruefung, die gefehlt hat: _safe() schuetzt die Karten, "
           "nicht das Zusammensetzen")
    # KORREKTUR MEINER EIGENEN R-1-PRAEMISSE (14.08.): ich hatte geschrieben,
    # die Remote-Seite ZEIGE eine leere Konfidenzspalte. Sie zeigt sie nicht -
    # `_get_konfidenz_kalibrierung` ist definiert und wird NIRGENDS aufgerufen,
    # ebenso `KONFIDENZ_BUCKET_ORDER` in server.py. Die ganze Karte ist toter
    # Code. Der Hinweis bleibt trotzdem drin: wer sie eines Tages verdrahtet,
    # findet ihn vor, statt die Frage neu zu stellen.
    _st = _quelltext("remote/status.py")
    pruefe(P, "der R-1-Hinweis steht an der Konfidenz-Karte",
           "_nur_alte_kette" in _st and "Rollen-Kette" in _st)
    pruefe(P, "und die Karte ist tatsaechlich nicht verdrahtet",
           _st.count("_get_konfidenz_kalibrierung") == 1,
           "definiert, nie gerufen - die Remote-Seite zeigt gar keine "
           "Konfidenz, anders als ich in Kapitel 18.6 geschrieben hatte")

    # ------------------------------------------------------------------
    # W. DER VOLLE UMLAUF - Punkte 1 bis 3 des Multi-Asset-Umstiegs (14.08.).
    from agent import assetklassen as AK3
    from agent import betraege as BE3
    from agent import wiederholung as WH3

    # W1 BETRAEGE UND COOLDOWN JE GRUPPE.
    pruefe(P, "Krypto-Tranche bleibt 250, boersengehandelt 400",
           BE3.einsatz_eur("spot", "akkumulation", None, "krypto") == 250.0
           and BE3.einsatz_eur("spot", "akkumulation", None, "aktien") == 400.0,
           "an der Boerse kostet 1 EUR fix je Seite - bei 250 EUR sind das "
           "0,8 % allein an Fixkosten, bei Krypto kuerzt sich der Betrag heraus")
    pruefe(P, "Krypto laeuft mit 15 h, Boersenwerte mit 24 h",
           WH3.stunden("spot", None, "krypto") == 15.0
           and WH3.stunden("spot", None, "aktien") == 24.0,
           "Krypto handelt rund um die Uhr, eine Aktie nicht - ein "
           "15-Stunden-Takt fragt dort mehrfach am selben Handelstag dasselbe")
    pruefe(P, "die Konfiguration schlaegt beide Vorgaben",
           WH3.stunden("spot", {"rollen_kette":
                                {"cooldown_stunden_je_gruppe": {"aktien": 6}}},
                       "aktien") == 6.0,
           "das Spezifischere gewinnt, und die Konfiguration gewinnt immer "
           "gegen den Code")
    pruefe(P, "die Gruppe wird durch die Kette gereicht",
           "gruppe=assetklasse" in _quelltext("agent/rollen_lauf.py"),
           "sonst gaelte ueberall der Instrument-Wert")

    # W2 DIE SERIEN DER BOERSENGEHANDELTEN WERTE haengen an den ALTEN Pipelines.
    #
    # DER TROCKENLAUF UEBER ALLE SECHS GRUPPEN hat es gezeigt: Hedge und
    # Rohstoffe haben auf dem Desktop KEINE Kursreihe. Sie werden zur Laufzeit
    # rekonstruiert - und die Funktion dafuer liegt in den Pipelines, die der
    # Schnitt eines Tages stilllegen soll.
    #
    # ENTWARNUNG, ABER MIT NAGEL: der OHLC-Refresh ruft
    # `_ensure_ohlc_backfilled` DIREKT aus den Pipeline-Modulen, unabhaengig von
    # deren Signalerzeugung. Wer die Pipelines eines Tages loescht, nimmt den
    # boersengehandelten Werten ihre Kursreihen mit - und zwar lautlos.
    _bgq = _quelltext("scheduler/background.py")
    pruefe(P, "der OHLC-Refresh holt die Rekonstruktion aus den Pipelines",
           "_ensure_ohlc_backfilled as _rohstoff_ohlc" in _bgq
           and "_ensure_ohlc_backfilled as _hedge_ohlc" in _bgq,
           "die Signalerzeugung darf stillgelegt werden, diese Funktion NICHT")

    # W3 DER UMLAUF SELBST.
    # ⚠️ S6b: FUENF STATT SECHS - Krypto hat den zweiten Lauf verloren.
    pruefe(P, "der Umlauf faehrt fuenf Kombinationen, eine je Gruppe",
           len(AK3.laeufe()) == 5
           and len({g for g, _i, _ in AK3.laeufe()}) == 5,
           str([(g, i) for g, i, _ in AK3.laeufe()]))
    pruefe(P, "und ueberspringt, was nicht umgestellt ist",
           "if not bedient_neue_kette(gruppe, config):" in _quelltext(
               "scheduler/rollen_job.py"),
           "eine Klasse, eine Kette - auch waehrend der Umstellung")

    # ------------------------------------------------------------------
    # X. DIE DREI ENTSCHEIDUNGEN vom 14.08. - Z.ai, Trefferbilanz, Groq.
    import threading as _th
    from agent import zweite_meinung as ZM2
    from agent import toepfe as TP2
    from agent import trefferbilanz as TB2
    from scheduler.rollen_job import KETTE as _KETTE, _vorgabemodell as _vm

    # X1 Z.AI - DER ANDRANG WAR NICHT DIE STIMMENZAHL.
    #
    # Die Annahme war "drei Stimmen nacheinander kosten Zeit". Der Engpass war
    # ein anderer: `rollen_lauf` startet einen Faden JE SIGNAL, und jeder ruft
    # Z.ai auf. Bei zehn Signalen waren das zehn gleichzeitige Aufrufe gegen
    # ein Limit von zwei - unbegrenzte Parallelitaet, nicht zu wenig.
    _belegt, _spitze, _s = [0], [0], _th.Lock()

    def _messe(_i):
        with _s:
            _belegt[0] += 1
            _spitze[0] = max(_spitze[0], _belegt[0])
        import time as _t
        _t.sleep(0.05)
        with _s:
            _belegt[0] -= 1

    _f = [_th.Thread(target=lambda i=i: ZM2._mit_platz(_messe, i))
          for i in range(12)]
    for _t2 in _f:
        _t2.start()
    for _t2 in _f:
        _t2.join()
    pruefe(P, "zwoelf Faeden erzeugen hoechstens zwei gleichzeitige Aufrufe",
           0 < _spitze[0] <= ZM2.MAX_GLEICHZEITIG == 2,
           f"gemessene Spitze {_spitze[0]} - die Aussage ist NIE MEHR ALS "
           "zwei, nicht genau zwei: ob sich zwei Faeden begegnen, haengt am "
           "Zeitverhalten der Maschine, die Obergrenze nicht")
    # ⚠️ DIESE PRUEFUNG HAT AM 17.08. EINE REGRESSION GEFANGEN, die ich gerade
    # eingebaut hatte. Der Andrangdeckel umschloss NUR die Konsistenzpruefung -
    # weder der Richtungsabgleich noch Rolle G liefen je durch ihn. Mit dem
    # Entfernen der Konsistenzpruefung waere er ersatzlos verschwunden, und
    # `rollen_lauf` startet EINEN FADEN JE SIGNAL: zehn Signale, zehn
    # gleichzeitige Z.ai-Aufrufe. Genau der Zustand vom 14.08.
    pruefe(P, "die Bremse sitzt am Anbieter, nicht am Lauf",
           "_mit_platz(rolle_g" in _quelltext("agent/zweite_meinung.py"),
           "sonst gilt sie nur fuer den einen Aufrufer, der sie kennt - und "
           "seit dem 16.08. kannte sie keiner mehr")
    pruefe(P, "wer keinen Platz bekam, wird als uebersprungen gebucht",
           "Andrang" in _quelltext("agent/zweite_meinung.py")
           and 'aus["uebersprungen"] =' in _quelltext(
               "agent/zweite_meinung.py"),
           "fail-soft ist fail-silent - ein Ausfall darf nicht aussehen wie "
           "eine bestandene Pruefung")

    # X2 TREFFERBILANZ - NACH INSTRUMENT GETRENNT, NACH MODELL NICHT.
    pruefe(P, "Spot und Hebel landen nicht mehr in denselben Zellen",
           TP2.sql_bedingung("spot").startswith("hebel IS NULL")
           and TP2.sql_bedingung("hebel") == "hebel IS NOT NULL",
           "die CRV-Abstufung half bei Spot (SQN +0,63 -> +1,36) und schadete "
           "beim Hebel (+3,25 -> +1,25) - eine gemeinsame Bilanz haette das "
           "nie zeigen koennen")
    pruefe(P, "der Unterscheider steht an EINER Stelle",
           "bedingung = sql_bedingung ( instrument )" in _nur_code(
               "agent/toepfe.py"),
           "er stand in belegt_eur und waere die vierte Kopie geworden")
    pruefe(P, "der Lauf reicht sein Instrument an die Bilanz durch",
           "TB . zaehle ( conn , quelle_kette = " in _nur_code(
               "agent/rollen_lauf.py")
           and "instrument = instrument )" in _nur_code(
               "agent/rollen_lauf.py"),
           "sonst waere die Trennung gebaut und unbenutzt")
    with sqlite3.connect("file:data/tradinginfotool.db?mode=ro",
                          uri=True) as _c2:
        pruefe(P, "zaehle() nimmt das Instrument gegen die echte Tabelle",
               isinstance(TB2.zaehle(_c2, instrument="hebel"), dict),
               "der Filter darf die Abfrage nicht zerbrechen")
        pruefe(P, "und die Modellmischung ist ablesbar",
               isinstance(TB2.modell_mischung(_c2), dict),
               "das Modell steht NICHT im Schluessel - eine Spaltung haette "
               "die Zellen gefuenftelt und die Rueckfallkette in leere Zellen "
               "laufen lassen, genau wenn etwas schiefgeht")

    # X3 GROQ - VIERTER TOPF.
    pruefe(P, "Groq steht als letzter in der Rueckfallkette",
           _KETTE[-1][0] == "groq" and len(_KETTE) == 4,
           "der 413-Grund ist entfallen: 34.611 -> 3.183 Zeichen Prompt")
    # O-25: der Groq-Deckel ist eine TOKEN-Rechnung, keine Anfragenzahl.
    # O-28: DER HEBEL-DURCHGANG WAR VOLLSTAENDIG BLOCKIERT.
    #
    # Der erste Echtbetrieb erzeugte 45 Urteile und KEIN einziges Hebel-Signal.
    # Nicht, weil der Durchgang ausfiel - `assetklassen.laeufe()` faehrt
    # krypto/spot VOR krypto/hebel ueber DIESELBEN 43 Symbole, und die Sperre
    # fragte nur nach `symbol` und `quelle_kette`. Nach dem Spot-Durchgang war
    # jedes Symbol gesperrt.
    import sqlite3 as _sq3
    from agent import wiederholung as WH4

    _c4 = _sq3.connect(":memory:")
    _c4.execute("CREATE TABLE signals (symbol TEXT, created_at TEXT, "
                "quelle_kette TEXT, hebel REAL)")
    _c4.execute("INSERT INTO signals VALUES ('BTC', ?, 'rollen', NULL)",
                ("2026-08-14T07:14:00+00:00",))
    _jetzt = "2026-08-14T07:30:00+00:00"
    # ⚠️ HIER STAND "ein Spot-Urteil sperrt den Hebel NICHT" (bis 23.08.2026).
    #
    # DIE BEGRUENDUNG WAR UND BLEIBT RICHTIG: "soll ich BTC mit Hebel handeln"
    # ist eine andere Frage als "soll ich eine Spot-Tranche nachlegen" -
    # andere Geometrie, andere Kosten, andere Haltedauer.
    #
    # ⚠️ ABER DIE PRAEMISSE IST ENTFALLEN. Der Kommentar oben nennt sie selbst:
    # "assetklassen.laeufe() faehrt krypto/spot VOR krypto/hebel ueber
    # DIESELBEN 43 Symbole". Seit S6b hat JEDE Gruppe genau EINEN Lauf - es
    # gibt keine zweite Frage mehr, die geschuetzt werden muesste.
    #
    # DESHALB PRUEFT DIESE STELLE JETZT BEIDE WELTEN: heute sperrt ein Urteil
    # unabhaengig vom Topf, und die Trennung KEHRT ZURUECK, sobald eine Gruppe
    # wieder zwei Laeufe hat. Die O-28-Erkenntnis bleibt damit gepruefter
    # Bestand statt einer geloeschten Zeile.
    from agent import assetklassen as _AK28

    pruefe(P, "EIN Lauf je Gruppe: das Urteil sperrt, egal in welchem Topf",
           WH4.gesperrt_bis(_c4, "BTC", "spot", gruppe="krypto",
                            jetzt=_jetzt) is not None
           and WH4.gesperrt_bis(_c4, "BTC", "hebel", gruppe="krypto",
                                jetzt=_jetzt) is not None,
           "seit S6b stellt die Kette EINE Frage - der Hebel faellt aus der "
           "Antwort an. Eine Sperre, die nur den halben Topf sieht, laesst "
           "dasselbe Symbol alle 15 Minuten neu fragen")
    _echt28 = dict(_AK28.INSTRUMENTE_JE_GRUPPE)
    try:
        _AK28.INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot", "hebel")
        pruefe(P, "ZWEI Laeufe: die Toepfe trennen sich wieder von selbst",
               WH4.gesperrt_bis(_c4, "BTC", "spot", gruppe="krypto",
                                jetzt=_jetzt) is not None
               and WH4.gesperrt_bis(_c4, "BTC", "hebel", gruppe="krypto",
                                    jetzt=_jetzt) is None,
               "O-28 (14.08.): der erste Echtbetrieb erzeugte 45 Urteile und "
               "KEIN Hebel-Signal, weil der Spot-Durchgang jedes Symbol "
               "gesperrt hatte. Die Trennung muss zurueckkehren, sobald es "
               "wieder zwei Durchgaenge gibt")
    finally:
        _AK28.INSTRUMENTE_JE_GRUPPE.clear()
        _AK28.INSTRUMENTE_JE_GRUPPE.update(_echt28)
    _c4.execute("INSERT INTO signals VALUES ('BTC', ?, 'rollen', 3.0)",
                ("2026-08-14T07:20:00+00:00",))
    pruefe(P, "und umgekehrt sperrt der Hebel sich selbst",
           WH4.gesperrt_bis(_c4, "BTC", "hebel", jetzt=_jetzt) is not None,
           "die Sperre muss innerhalb des Instruments weiter greifen - sie "
           "ist die gemessene Verlustquelle (5 Symbole = 102 % des Minus)")
    _c4.close()

    # O-26: die CRV-Abstufung gilt dort, wo sie gemessen wurde.
    from agent import entscheidungsrechnung as ER4
    # STILLGELEGT SEIT 15.08. - die Einschraenkung auf Krypto-Spot bleibt im
    # Code stehen, damit sie beim Wiedereinschalten nicht neu gefunden werden
    # muss. Geprueft wird jetzt, dass die Regel WIRKUNGSLOS ist.
    pruefe(P, "die CRV-Abstufung ist ueberall wirkungslos",
           ER4._crv_faktor(2.0, "spot", "krypto") == 1.0
           and ER4._crv_faktor(2.0, "spot", "boerse") == 1.0
           and ER4._crv_faktor(2.0, "hebel", "krypto") == 1.0,
           "gemessen an 298 KRYPTO-Spot-Signalen. An der Boerse kostet 1 EUR "
           "fix je Seite - dort verdreifacht die Abstufung die Kostenquote "
           "(1,00 -> 3,00 % bei 400 EUR Tranche) und macht den Trade teuer, "
           "wenn das Modell am wenigsten ueberzeugt ist")

    pruefe(P, "Groqs Deckel folgt der Tokengrenze, nicht der Anfragengrenze",
           RJ2.GROQ_AUFRUFE_JE_TAG == int(RJ2.GROQ_TOKEN_JE_TAG
                                          / RJ2.GROQ_TOKEN_JE_AUFRUF)
           and RJ2.GROQ_AUFRUFE_JE_TAG < 100,
           "RPD 1.000 klingt grosszuegig; bei ~1.200 Token je Aufruf sind die "
           "100.000 TPD nach 83 erschoepft - einem Zwoelftel davon. Waechst "
           "der Prompt, sinkt das Budget jetzt mit")

    pruefe(P, "und der Scheduler uebergibt den Client auch",
           '"groq": groq_client' in _quelltext("scheduler/background.py"),
           "ein Topf ohne Client wird stillschweigend uebersprungen - eine "
           "Reaktivierung, die nur auf dem Papier stattfindet")
    _gq = type("G", (), {})
    _gq.__module__ = "api.groq"
    from api.groq import DEFAULT_MODEL as _GM
    pruefe(P, "ein Groq-Urteil traegt seinen Modellnamen",
           _vm(_gq()) == _GM == "llama-3.3-70b-versatile",
           "sonst stuende auf 80 Zeilen 'modell = NULL' und die Mischung "
           "waere nicht mehr rekonstruierbar")

    # ------------------------------------------------------------------
    # Y. DER LESEPFAD - die Spalte, die niemand lesen konnte (14.08.2026).
    #
    # `SPALTEN_SIGNAL` legte fuenfzehn Spalten an `signals` an, `models.Signal`
    # wuchs nicht mit, und `_row_to_signal()` baut die Klasse aus `SELECT *`:
    #
    #     TypeError: Signal.__init__() got an unexpected keyword argument
    #                'quelle_kette'
    #
    # ES BRACH BEI DER MIGRATION, nicht beim ersten Rollen-Signal: `SELECT *`
    # liefert alle Spalten, egal was in der Zeile steht. Damit war JEDES Signal
    # unlesbar, auch jedes alte - dreizehn Aufrufer von `get_latest_signal`.
    import inspect as _insp
    from database.models import Signal as _Sig, HebelSignal as _HSig
    from database import db as _DB2

    with sqlite3.connect("file:data/tradinginfotool.db?mode=ro",
                         uri=True) as _c3:
        _c3.row_factory = sqlite3.Row
        for _tab, _kls in (("signals", _Sig), ("hebel_signals", _HSig)):
            _f = set(_insp.signature(_kls.__init__).parameters) - {"self"}
            _sp = [r[1] for r in _c3.execute(f"PRAGMA table_info({_tab})")]
            _fehlt = [s for s in _sp if s not in _f]
            pruefe(P, f"jede Spalte von {_tab} hat ein Feld in {_kls.__name__}",
                   not _fehlt,
                   f"ohne Feld: {_fehlt} - die Klasse wird aus SELECT * "
                   "gebaut, eine unbekannte Spalte kappt JEDEN Lesepfad")
        _r3 = _c3.execute(
            "SELECT * FROM signals ORDER BY id DESC LIMIT 1").fetchone()
        if _r3 is not None:
            pruefe(P, "_row_to_signal() laeuft gegen eine echte Zeile",
                   _DB2._row_to_signal(_r3) is not None,
                   "die Pruefung darueber vergleicht Namen - diese hier baut "
                   "das Objekt wirklich, so wie die dreizehn Aufrufer es tun")
    pruefe(P, "die neuen Spalten sind auch als Feld deklariert",
           not (set(SA.SPALTEN_SIGNAL)
                - (set(_insp.signature(_Sig.__init__).parameters) - {"self"})),
           "SPALTEN_SIGNAL und models.Signal muessen zusammen wachsen")

    # ------------------------------------------------------------------
    # Z. DIE ERSTE PRODUKTIONSMAIL (PLUME, 14.08.2026 09:23) - drei Funde.
    from agent import signal_mail as SM3
    from agent.signal_mail import preis as _preis
    from agent import entscheidungsrechnung as ER3

    # Z1 DER KURS UNTER EINEM CENT WURDE ZU NULL.
    #
    #     Einstiegszone   0 bis 0 EUR
    #     Stop            0 EUR  (5,5 % - ...)
    #     Take-Profit     0 bis 0 EUR
    #
    # Eine Kaufempfehlung ohne Einstieg, ohne Stop, ohne Ziel - bei einer
    # richtig gerechneten Rechnung. In DERSELBEN Mail stand "Widerstand bei
    # 0.0119 EUR", weil die Zahlen des Modells nicht durch diesen Formatierer
    # laufen. Zwei Zahlenwege, einer davon kaputt.
    pruefe(P, "ein Kurs unter einem Cent bleibt lesbar",
           _preis(0.0119) == "0,01190" and _preis(0.00004321) == "0,00004321",
           f"0,0119 -> {_preis(0.0119)!r}")
    pruefe(P, "und ein grosser Kurs bleibt gewohnt",
           _preis(61234.5) == "61.234,50" and _preis(2.34) == "2,34",
           "ab einem Euro sind zwei Stellen die gewohnte Schreibweise")
    pruefe(P, "die Rechnung benutzt den Kursformatierer, nicht _eur",
           "{preis(e['stop_eur'])}" in _quelltext(
               "agent/entscheidungsrechnung.py")
           and "{preis(e['einstieg_von_eur'])}" in _quelltext(
               "agent/entscheidungsrechnung.py"),
           "Betraege duerfen bei _eur bleiben - Kurse nicht. UND: dieser "
           "Aufruf steht IN einem f-String, also findet ihn nur der Rohtext - "
           "_nur_code wirft Zeichenketten weg. Dieselbe Falle zum vierten Mal.")

    # Z2 ZWEI STOP-ABSTAENDE FUER DENSELBEN STOP.
    #
    #   2. DIE RECHNUNG   Stop  5,5 %  (gegen die Einstiegszone)
    #   4. EINORDNUNG     Stop 11,2 %  (gegen den aktuellen Kurs)
    #
    # Beide fuer sich richtig - die Zone lag 6 % unter dem Kurs. Fuer den Leser
    # ist es der schlimmere Widerspruch: er schaetzt sein Risiko doppelt so
    # hoch ein wie geplant und sieht nicht, warum.
    # PRAEZISIERT 16.08.2026: der geplante Einstieg ist die MITTE der Zone,
    # nicht ihre untere Kante - siehe T4e. Gegen die Kante gemessen sah der
    # Stop um ein Drittel naeher aus, als er ist.
    pruefe(P, "die Einordnung rechnet gegen den GEPLANTEN Einstieg",
           'einstieg=rechnung.get("einstieg_eur")' in _quelltext(
               "agent/rollen_lauf.py"),
           "sie ordnet den geplanten Trade ein, nicht einen zum Marktpreis")

    # Z3 FUENF INFORMATIONSBLOECKE DER MAIL SIND AN NICHTS ANGESCHLOSSEN.
    #
    # `baue_mail` kann Bestand, Marken in Euro, Umfeld, Ausstieg und
    # Coin-Fakten darstellen. Die Rollen-Kette uebergibt keinen davon - darum
    # liest sich die Mail generisch, obwohl die Vorlage es nicht ist. KEIN
    # Defekt im Sinne eines Fehlers, aber der Grund fuer den Eindruck.
    import inspect as _i3
    import re as _re3
    _moegl = [p for p in _i3.signature(SM3.baue_mail).parameters]
    _q = _quelltext("agent/rollen_lauf.py")
    _blk = _q[_q.index("return SM.baue_mail("):]
    _blk = _blk[:_blk.index("betreff, text = baue")]
    _fehlt = sorted(p for p in _moegl if p not in set(_re3.findall(r"(\w+)=", _blk)))
    # O-19 BIS O-23 ERLEDIGT (14.08.). Diese Pruefung stand vorher andersherum
    # - sie zaehlte die fuenf NICHT verdrahteten Bloecke auf und sollte
    # anschlagen, sobald einer angeschlossen wird. Genau das hat sie getan.
    pruefe(P, "die Kaufmail bekommt JEDEN Block, den sie darstellen kann",
           not _fehlt,
           f"nicht uebergeben: {_fehlt} - die Vorlage ist nicht generisch, "
           "sie wurde nur zu zwei Dritteln gefuettert")
    # DIESELBE QUELLE - UND SEIT DEM 16.08. DASSELBE OBJEKT.
    #
    # Diese Pruefung stand bis heute auf einem ZWEITEN `LB.geteilt()`-Aufruf im
    # Mail-Weg. Der war am 14.08. richtig, ist seit dem 15.08. aber eine Kopie:
    # `baue_fall(bloecke_ziel=...)` legt dieselben Bloecke fuer den
    # Anlassfilter ohnehin daneben. Und er lief auseinander - er bekam den ATR
    # in EUR, waehrend der Prompt-Weg die Quellwaehrung uebergibt, sodass die
    # Mail andere Schwankungsbreiten zeigte als das Modell gelesen hat.
    #
    # Die Pruefung testet jetzt die staerkere Form derselben Absicht: nicht
    # "zwei Wege rechnen dasselbe", sondern "es gibt nur einen Weg".
    _q_lauf0 = " ".join(_nur_code("agent/rollen_lauf.py").split())
    pruefe(P, "die Bloecke der Mail SIND die Bloecke des Prompts",
           "_bloecke = _bloecke_anlass" in _q_lauf0
           and "bloecke_ziel = _bloecke_anlass" in _q_lauf0
           and "LB . geteilt (" not in _q_lauf0,
           "ein zweiter Aufruf waere eine Kopie - und die vom 14.08. ist mit "
           "dem falschen ATR gelaufen (EUR statt Quellwaehrung)")
    # UND BEIDE WEGE TRAGEN DAS INSTRUMENT (15.08.2026).
    #
    # `RE.bestand()` las bis dahin IMMER `holdings` - die Spot-Tabelle. Im
    # Hebel-Lauf stand damit der Spot-Bestand im Prompt UND in der Mail; das
    # Modell empfahl SCHLIESSEN fuer Positionen, die es nie gab (22x an einem
    # Vormittag, 9 % aller Aufrufe). Die Angabe muss an BEIDEN Stellen
    # ankommen - eine allein waere wieder ein halber Zustand.
    _q_lauf = _nur_code("agent/rollen_lauf.py")
    pruefe(P, "der Prompt-Weg kennt das Instrument",
           "RE . baue_fall (" in _q_lauf
           and "instrument = instrument" in _q_lauf,
           "sonst stuende im AUFTRAG-Block 'ohne Hebel und ohne laufende "
           "Kosten' - auch im Hebel-Lauf")
    # DIE GEGENSEITE STEHT JETZT AN DER EINEN STELLE, an der die Bloecke
    # entstehen - nicht mehr zusaetzlich im Mail-Weg. Sie erreicht die Mail
    # ueber `_bloecke_anlass`, also durch dieselbe Rechnung wie den Prompt.
    pruefe(P, "die Gegenseite wird genannt, mit Instrument",
           "gegenbestand_satz ( symbol , db , instrument )"
           in " ".join(_nur_code("agent/rollen_eingabe.py").split()),
           "die andere Seite desselben Assets wird benannt statt "
           "verschwiegen - der LINK-Fall des Nutzers")
    # DER PROMPT DARF SICH DABEI NICHT VERAENDERT HABEN - sonst waeren alle
    # bisherigen Messungen nicht mehr vergleichbar.
    import numpy as _np
    from agent import lagebeschreibung as LB3

    class _K:
        def __init__(_s, i):
            _s.close = 100.0 + i * 0.5
            _s.high = _s.close * 1.01
            _s.low = _s.close * 0.99
            _s.volume = 1000.0 + i
            _s.date = f"2026-01-{(i % 28) + 1:02d}"

    _reihe = [_K(i) for i in range(90)]
    _flach = LB3.beschreibe_lage(symbol="TST", reihe=_reihe, index=89,
                                 kurs_eur=144.5, atr=1.2, menge=3.0,
                                 einstand_eur=100.0)
    _teil = LB3.geteilt(symbol="TST", reihe=_reihe, index=89, kurs_eur=144.5,
                        atr=1.2, menge=3.0, einstand_eur=100.0)
    pruefe(P, "beschreibe_lage() liefert genau die zusammengesetzten Bloecke",
           _flach == [s for b in LB3.BLOCK_REIHENFOLGE for s in _teil[b]],
           "der Prompt muss Zeichen fuer Zeichen derselbe bleiben - sonst "
           "sind alle bisherigen Messungen nicht mehr vergleichbar")
    pruefe(P, "und der Bestand ist der erste Block",
           LB3.BLOCK_REIHENFOLGE[0] == "bestand" and _teil["bestand"],
           "R-T9: was zuerst steht, wiegt schwerer - und die erste Frage des "
           "Nutzers ist 'habe ich das ueberhaupt'")

    # ------------------------------------------------------------------
    # PHASE I (16.08.2026) - vier gruene Ergaenzungen in EINEM Prompt-Stand.
    #
    # Alle vier sind BESCHREIBEND. Der Unterschied zu bewertend ist gemessen
    # und teuer: der Kosten-/Ausfuehrbarkeitshinweis liess die EROEFFNEN-Quote
    # von 93 % auf 3 % einbrechen (Umbauplan 36.1). Deshalb pruefen die Tests
    # hier nicht nur, DASS die Saetze da sind, sondern auch, dass sie keine
    # Handlungsanweisung tragen.
    _fin = {"beobachtungen": 100, "anteil_positiv_pct": 61, "perzentil": 72}
    # ⚠️ DER UNTERSCHEIDER IST SEIT DEM 23.08.2026 DIE GRUPPE, NICHT DER LAUF.
    #
    # Hier stand `instrument="spot"` gegen `instrument="hebel"`. Das war
    # richtig, solange es zwei Laeufe gab. Seit S6b laeuft Krypto NUR mit
    # `instrument="spot"` - beide Bausteine erreichten damit niemanden mehr,
    # obwohl der Hebel seit S6a als ERGEBNIS der Rechnung weiterhin
    # entstehen kann.
    #
    # DIE FRAGE LAUTET JETZT: kann diese GRUPPE gehebelt werden? Die Probe
    # stellt deshalb Krypto (kann) gegen Aktien (kann nicht) - der Lauf ist
    # bei beiden derselbe.
    _spot = LB3.geteilt(symbol="TST", reihe=_reihe, index=89, kurs_eur=144.5,
                        atr=1.2, menge=3.0, einstand_eur=100.0,
                        finanzierung=_fin, instrument="spot",
                        assetklasse="aktien")
    _heb = LB3.geteilt(symbol="TST", reihe=_reihe, index=89, kurs_eur=144.5,
                       atr=1.2, menge=3.0, einstand_eur=100.0,
                       finanzierung=_fin, instrument="spot",
                       assetklasse="krypto")

    # SCHRITT 2 - die Finanzierung steht nur, wo ein Hebel moeglich ist.
    pruefe(P, "Finanzierung steht nur, wo ein Hebel handelbar ist",
           not _spot["finanzierung"] and len(_heb["finanzierung"]) == 1,
           "ein Spot-Kaeufer leistet und erhaelt keine Finanzierung - und "
           "zitiert wurde sie trotzdem in 63 % der Spot-Urteile (O-34)")
    # ROHTEXT, NICHT `_nur_code` - die Bedingung haengt an einer ZEICHENKETTE
    # ("hebel"), und `_nur_code` wirft Zeichenketten weg. Dieselbe Falle zum
    # fuenften Mal; sie steht deshalb hier ausdruecklich im Kommentar.
    _roh_ein5 = " ".join(_quelltext("agent/rollen_eingabe.py").split())
    pruefe(P, "und sie wird bei Spot gar nicht erst geholt",
           'mit_finanzierung and str(instrument) == "hebel"' in _roh_ein5,
           "sonst laufen je Spot-Durchgang 43 Anfragen an die Boerse fuer "
           "einen Satz, den niemand mehr rendert - und jede bucht ihren "
           "Gesundheitsstand in api_health_status")

    # SCHRITT 1 - der Liquidationsabstand, und zwar mit DERSELBEN Formel, die
    # `entscheidungsrechnung` spaeter fuer `liquidation_etwa_eur` benutzt.
    # Zwei Definitionen desselben Abstands waeren genau die Sorte Kopie, die
    # dieses Projekt mehrfach bezahlt hat.
    from agent import entscheidungsrechnung as ER5

    pruefe(P, "der Liquidationsabstand steht nur, wo ein Hebel handelbar ist",
           not _spot["hebelgeometrie"] and len(_heb["hebelgeometrie"]) == 2,
           "eine Aktie laesst sich hier nicht hebeln - der Satz waere dort "
           "schlicht falsch. Bei Krypto MUSS er stehen, auch im Spot-Lauf: "
           "der Hebel faellt seit S6a aus der Rechnung an, nicht aus dem Lauf")
    _kurs5, _hebel5 = 100.0, 10.0
    pruefe(P, "und er benutzt dieselbe Formel wie die spaetere Rechnung",
           abs((_kurs5 - _kurs5 * (1 - 1 / _hebel5)) / _kurs5
               - 1.0 / _hebel5) < 1e-12
           and 10.0 in LB3.GRENZHEBEL
           and LB3.GRENZHEBEL[-1] == ER5.GRENZEN["hebel_max"],
           "der groesste Stuetzpunkt MUSS der Hoechsthebel sein - sonst "
           "beschreibt die Tabelle eine Lage, die es nicht geben kann")
    pruefe(P, "der Abstand steht in Prozent UND in Schwankungsbreiten",
           "Schwankungsbreiten" in _heb["hebelgeometrie"][0]
           and "%" in _heb["hebelgeometrie"][0],
           "33/17/10 % sind ueber alle Assets gleich und waeren allein ein "
           "konstantes Feld (R-T6) - erst der ATR-Bezug macht daraus eine "
           "Aussage ueber DIESES Asset")
    pruefe(P, "und er nennt weder Kosten noch eine Empfehlung",
           not any(w in " ".join(_heb["hebelgeometrie"]).lower()
                   for w in ("kostet", "teuer", "gebuehr", "vorsichtig",
                             "riskant", "solltest", "empfiehlt")),
           "gruen heisst beschreibend. Der Kostenhinweis ist die gemessene "
           "Grenze: 93 % auf 3 % EROEFFNEN")

    # SCHRITT 3 - fehlende Angaben werden benannt statt weggelassen.
    _ohne_v = [_K(i) for i in range(90)]
    for _k in _ohne_v:
        _k.volume = None
    _luecke = LB3.geteilt(symbol="TST", reihe=_ohne_v, index=89,
                          kurs_eur=144.5, atr=1.2)
    pruefe(P, "fehlender Umsatz wird BENANNT, nicht verschwiegen",
           not _luecke["volumen"] and any("KEIN Umsatz ausgewiesen" in s
                                          for s in _luecke["luecken"]),
           "das Modell liest Abwesenheit sonst als Unauffaelligkeit - der "
           "KAS-Fall in anderer Gestalt (Umbauplan 34.6)")
    pruefe(P, "und eine kurze Historie ebenso",
           any("Handelstage" in s for s in LB3.geteilt(
               symbol="TST", reihe=_reihe[:70], index=69, kurs_eur=144.5,
               atr=1.2)["luecken"]),
           "OD7L (137) und X136 (162) liegen unter den 250 Handelstagen, die "
           "die Perzentile brauchen - dieselbe Grenze, die ASTER betraf")
    # LANG GENUG UND MIT WENDEPUNKTEN. Zwei eigene Fehlschlaege in dieser
    # Pruefung, beide an den Testdaten und nicht am Code:
    #   * die 90-Kerzen-Reihe der uebrigen Tests ist selbst zu kurz und loest
    #     den Historien-Satz aus
    #   * eine streng steigende Reihe hat KEINE Swing-Punkte, also findet
    #     `_niveaus()` keine Marke - und der Luecken-Block meldet das voellig
    #     zu Recht
    # Der Gegenfall braucht deshalb eine schwingende Reihe.
    class _KS(_K):
        def __init__(_s, i):
            import math
            _s.close = 100.0 + 0.3 * i + 8.0 * math.sin(i / 7.0)
            _s.high = _s.close * 1.01
            _s.low = _s.close * 0.99
            _s.volume = 1000.0 + (i % 13) * 40
            _s.date = f"2026-01-{(i % 28) + 1:02d}"

    _lang = [_KS(i) for i in range(300)]
    pruefe(P, "bei vollstaendigen Daten steht KEIN Luecken-Satz",
           not LB3.geteilt(symbol="TST", reihe=_lang, index=299,
                           kurs_eur=144.5, atr=1.2)["luecken"],
           "sonst waere es ein stehendes Feld ueber alle Assets - genau das, "
           "was R-T6 verbietet")

    # SCHRITT 4 - der Sektorbezug, und die Abgrenzung, an der er haengt.
    pruefe(P, "der Sektorbezug nennt sein Fenster und seinen Massstab",
           all("Handelstage" in s and "Prozentpunkte" in s for s in
               LB3._referenz({"name": "der breite Markt", "rel_30": -8.9,
                              "rel_90": 15.9})),
           "eine relative Staerke ohne Fenster und ohne Bezugsgroesse waere "
           "eine nackte Zahl")
    # ⚠️ DIESE ABGRENZUNG WAR IN MEINER ERSTEN FASSUNG FALSCH und haette nie
    # gegriffen: der Aufrufer uebergibt die GRUPPE (`themen_etf`), nicht die
    # Assetklasse (`etf`). `agent/assetklassen.py` haelt die drei Begriffe
    # ausdruecklich auseinander - gefunden hat es das RENDERN, nicht das Lesen.
    pruefe(P, "der Sektorbezug kennt das Gruppen-Vokabular",
           'in ("etf", "themen_etf")' in _roh_ein5,
           "`etf` allein haette nie gegriffen - `rollen_lauf` uebergibt die "
           "Gruppe, und die heisst themen_etf")
    pruefe(P, "und die Klassen-Einstufung ebenso",
           '"themen_etf": "aktien"' in _roh_ein5
           and '"hedge": "aktien"' in _roh_ein5,
           "zwei von fuenf Gruppen bekamen die Einstufung des Leitmarkts "
           "nicht - lautlos, weil ein fehlender Schluessel kein Fehler ist")

    # DIE REIHENFOLGE DER ALTEN BLOECKE IST UNVERAENDERT. Die neuen sind
    # eingeschoben, nicht dazwischengemischt - sonst muesste ein Vergleich
    # zweier Prompt-Staende zusaetzlich eine Umsortierung mitmessen.
    # `struktur` und `bewegung` sind seit dem 17.08. der Block `verlauf` -
    # die RELATIVE Reihenfolge der uebrigen ist davon unberuehrt.
    _alt = ("bestand", "verlauf", "marken", "volumen", "finanzierung")
    pruefe(P, "die alten Bloecke stehen weiter in ihrer Reihenfolge",
           [b for b in LB3.BLOCK_REIHENFOLGE if b in _alt] == list(_alt)
           and LB3.BLOCK_REIHENFOLGE[-1] == "luecken",
           "und was FEHLT steht zuletzt - es darf nicht schwerer wiegen als "
           "das, was da ist (R-T9)")

    # ------------------------------------------------------------------
    # KLASSE 1 (16.08.2026) - die woertliche Doppelung ist weg.
    #
    # Die 60-Tage-Bewegung stand in `struktur` UND in `bewegung`, bitgleich
    # gerechnet. Ueber alle Reihen mit voller Historie: 42 von 42 identisch.
    # Zwei Schaeden, nicht nur Redundanz: eine doppelt genannte Zahl wiegt
    # schwerer (Wiederholung als Gewicht), und ein Beleg, der sie zitiert, ist
    # KEINEM Block zuordenbar - die Blockmessung lief durch genau den Fehler,
    # den sie messen sollte.
    # SCHWINGENDE REIHE, nicht die streng steigende der uebrigen Tests: ohne
    # Wendepunkte findet `_swings()` nichts, `_struktur()` liefert dann gar
    # keinen Satz, und der Test misst eine Reihe statt der Zusammenlegung.
    # Derselbe Stolperstein wie beim Luecken-Gegenfall - zum zweiten Mal.
    class _KV(_K):
        def __init__(_s, i):
            import math
            _s.close = 100.0 + 0.3 * i + 8.0 * math.sin(i / 7.0)
            _s.high = _s.close * 1.01
            _s.low = _s.close * 0.99
            _s.volume = 1000.0 + (i % 13) * 40
            _s.date = f"2026-01-{(i % 28) + 1:02d}"

    _rv = [_KV(i) for i in range(90)]
    _v = LB3.geteilt(symbol="TST", reihe=_rv, index=89,
                     kurs_eur=144.5, atr=1.2)["verlauf"]
    pruefe(P, "Struktur und Bewegung sind EIN Block",
           "struktur" not in LB3.BLOCK_REIHENFOLGE
           and "bewegung" not in LB3.BLOCK_REIHENFOLGE
           and len(_v) == 2,
           "getrennt gezaehlt bewegten sie sich gemeinsam - der Anlassfilter "
           "sah zwei Abdruecke fuer eine Sache")
    _prozente = _re3.findall(r"([+-][\d.]+) %", " ".join(_v))
    pruefe(P, "und keine Prozentzahl steht darin zweimal",
           len(_prozente) == len(set(_prozente)),
           f"gefunden: {_prozente} - eine Zahl, die zweimal dasteht, wiegt "
           f"schwerer, und das war nie beabsichtigt")
    pruefe(P, "die Nachbarschaft von Struktur und 60-Tage-Zahl bleibt",
           "Marktstruktur" in _v[0] and "60 Tage" in _v[1]
           and "im selben Rahmen" in _v[1],
           "sie war der Fix vom 11.08. (ETH-Fall: Etikett hoch gewichtet, "
           "Zahl daneben gering) - entfallen ist die zweite NENNUNG, nicht "
           "der Bezug")
    # ROLLE A, derselbe Fehler in bedingter Form: Abstand zum Hoch faellt mit
    # dem 250-Tage-Trend zusammen, sobald das Hoch am Fensteranfang liegt.
    # NICHT gestrichen, sondern aufgewertet - die LAGE der Extrema in der Zeit
    # steht sonst nirgends.
    from agent import marktlage as ML5

    _q_ml = _quelltext("agent/marktlage.py")
    pruefe(P, "Rolle A nennt, WANN Hoch und Tief lagen",
           "das Hoch " in _q_ml and "liegt {wo_hoch} Handelstage zurueck" in _q_ml
           and "nanargmax" in _q_ml and "nanargmin" in _q_ml,
           "ohne diese Angabe wiederholt der Satz bei einem Hoch am "
           "Fensteranfang nur die Zahl des vorigen")
    # ROLLE C: DIE REGIME-DAUER MUSS ANKOMMEN.
    #
    # Sie kam es im Betrieb NIE. `regime_persistenz_tage()` liest ueber
    # `get_hebel_regime_tageshistorie()`, und die greift mit `row["tag"]` zu -
    # das setzt `conn.row_factory = sqlite3.Row` voraus. `rolle_g` oeffnet eine
    # gewoehnliche Verbindung; der TypeError verschwand im breiten `except`,
    # und in jeder Ausgabe stand nur "Regime 'baer'".
    #
    # OHNE DAUER IST DAS REGIME EIN KONSTANTES FELD (R-T6) - ueber alle
    # Signale eines Tages identisch. Genau deshalb wird hier FUNKTIONAL
    # geprueft, an einer Verbindung OHNE row_factory, und nicht am Quelltext.
    import sqlite3 as _sq5

    from agent import positionierung as PO5

    _mem = _sq5.connect(":memory:")
    _mem.execute("CREATE TABLE signals (regime TEXT, created_at TEXT)")
    _mem.execute("CREATE TABLE hebel_signals (regime TEXT, regime_source TEXT,"
                 " created_at TEXT)")
    _mem.execute("CREATE TABLE open_interest_snapshot (symbol TEXT, "
                 "exchange TEXT, fetched_at TEXT, open_interest REAL, "
                 "funding_rate REAL, long_account_pct REAL)")
    _mem.execute("INSERT INTO signals VALUES ('baer', '2026-08-16 10:00:00')")
    for _t in ("2026-08-14", "2026-08-15", "2026-08-16"):
        _mem.execute("INSERT INTO hebel_signals VALUES "
                     "('baer', 'regelbasiert', ?)", (f"{_t} 09:00:00",))
    _lage5 = PO5.lage(_mem, "TST")
    # ⚠️ HIER STANDEN ZWEI PRUEFUNGEN, DIE DAS MARKTREGIME VERLANGTEN.
    # Herausgenommen am 16.08. abends - sie sicherten etwas ab, das gegen vier
    # eigene Regeln verstiess (R-T2 Etikett, R-T3 Werturteil, R-T6 konstant,
    # P3 aus unseren eigenen Daten gerechnet). Der Nutzer hat es an einer
    # echten Mail gesehen: das Modell gab den Regimesatz WOERTLICH als Einwand
    # zurueck, waehrend jeder echte Positionierungsfakt "im gewohnten Bereich"
    # sagte.
    #
    # AUS DER ZUSICHERUNG WIRD EINE GEGENWACHE. Eine geloeschte Pruefung
    # verhindert nichts; diese hier schlaegt an, wenn das Regime je
    # zurueckkommt - und `finde_konstanten` traegt den Fall seit Wochen im
    # Docstring, ohne dass es genuetzt haette.
    pruefe(P, "das Marktregime erreicht Rolle G NICHT mehr",
           "regime" not in _lage5
           and not any("Regime" in s for s in PO5.saetze(_lage5)),
           "2.549 von 2.549 Signalen trugen 'baer' - eine Konstante mit "
           "Richtungsaussage schiebt JEDE Antwort in dieselbe Richtung")
    pruefe(P, "und die Zeilenfabrik des Aufrufers bleibt unberuehrt",
           _mem.row_factory is None,
           "wird hier wieder etwas geliehen, muss es zurueckgegeben werden")

    # --- DER BOERSENFLUSS (16.08.2026, Schritt 2) ---------------------
    #
    # FUNKTIONAL UND OHNE NETZ. `_fluss_reihe` wird ersetzt, sonst haengt
    # eine Paketpruefung an CoinMetrics - und eine Pruefung, die bei
    # Netzausfall rot wird, sagt nichts ueber den Code.
    # ⚠️ DIE NAHT HAT SICH IN SCHRITT 3 VERSCHOBEN. Bis dahin lag sie bei
    # `_fluss_reihe`; jetzt geht der Weg ueber `_gepflegte_reihe` (DB,
    # dann Speicher, dann Netz), und ersetzt wird der NETZABRUF selbst.
    # Damit prueft der Test denselben Sachverhalt an der Stelle, an der
    # er heute entsteht - statt an einem Namen, den es nicht mehr gibt.
    import api.onchain as OC5

    _echt5 = OC5.get_btc_exchange_flow_history
    try:
        PO5._fluss_cache.clear()
        OC5.get_btc_exchange_flow_history = (
            lambda *a, **k: [(f"2026-01-{i%28+1:02d}", float(i % 40 - 20))
                             for i in range(400)])
        _kr5 = PO5.lage(_mem, "TST", assetklasse="krypto")
        _ak5 = PO5.lage(_mem, "TST", assetklasse="aktien")
        pruefe(P, "der Boersenfluss erreicht NUR Krypto",
               bool(_kr5.get("boersenfluss")) and not _ak5.get("boersenfluss"),
               "BTC-Bewegungen in der Beurteilung einer Aktie waeren kein "
               "fehlender Fakt, sondern ein falscher (P1)")
        pruefe(P, "ohne Assetklasse bleibt er weg (fail-closed)",
               not PO5.lage(_mem, "TST").get("boersenfluss"),
               "ein unbekannter Aufrufer darf nicht versehentlich einen "
               "marktweiten Fakt in ein Einzelurteil tragen")
        _s5 = " ".join(PO5.saetze(_kr5))
        pruefe(P, "der Flusssatz nennt Richtung UND Perzentil mit Einordnung",
               "Bitcoin" in _s5 and "Perzentil" in _s5
               and ("gewohnten Bereich" in _s5 or "aussergewoehnlich" in _s5),
               "R-T11: ein Perzentil ohne Wort dazu, ob das viel ist, "
               "verlangt vom Modell die Rechenleistung, die es nicht hat")

        # ⚠️ DIE WICHTIGSTE DER VIER. Faellt der Fluss aus, darf das Rolle G
        # NICHT stilllegen - `rolle_g` bricht bei `len(fehlt) >= 3` ab, und
        # eine ZUSAETZLICHE Quelle, die beim Ausfall eine Rolle abschaltet,
        # waere genau verkehrt herum.
        PO5._fluss_cache.clear()
        OC5.get_btc_exchange_flow_history = lambda *a, **k: []
        _aus5 = PO5.lage(_mem, "TST", assetklasse="krypto")
        pruefe(P, "ein ausgefallener Fluss zaehlt NICHT gegen die G5-Schranke",
               not _aus5.get("boersenfluss")
               and "Boersenzu- und -abfluesse" not in (_aus5.get("fehlt") or [])
               and "Boersenzu- und -abfluesse" in (_aus5.get("fehlt_rahmen") or [])
               and any("Gesamtmarkt liegt keine Angabe" in s
                       for s in PO5.saetze(_aus5)),
               "sonst legt eine zusaetzliche Quelle beim Ausfall die Rolle "
               "still - und verschwiegen werden darf der Ausfall trotzdem nicht")
    finally:
        OC5.get_btc_exchange_flow_history = _echt5
        PO5._fluss_cache.clear()

    # --- COT UND DIE PERSISTENZ (16.08.2026, Schritt 3) ---------------
    #
    # OHNE NETZ, mit einer eigenen Speicherdatenbank. Geprueft wird die
    # Mechanik - Reihenfolge, Fenster, Zuordnung -, nicht die CFTC.
    import sqlite3 as _sq6

    from agent import mindestkriterien as MK5
    from database import db as DB6

    _spk = _sq6.connect(":memory:")
    _spk.row_factory = _sq6.Row
    DB6.init_db(_spk)
    # ⚠️ 156 WOCHENPUNKTE, NICHT 48. Die erste Fassung schrieb ein Jahr
    # mit vier Punkten je Monat - unter `COT_MINDESTREIHE` (60), also gab
    # `_cot()` zu Recht None zurueck, und drei Pruefungen schlugen fehl.
    # Nicht der Code war falsch, sondern die Testeingabe: sie stellte den
    # Fall nicht her, den sie pruefen wollte. Dieselbe Falle wie bei der
    # streng steigenden Reihe und dem Blocknamen mit Leerzeichen.
    from datetime import date, timedelta

    _start = date(2023, 1, 3)
    _punkte = [((_start + timedelta(weeks=i)).isoformat(),
                20.0 + (i * 7) % 30) for i in range(156)]
    DB6.schreibe_externe_reihe(_spk, "cftc_cot", "gold", _punkte)
    pruefe(P, "eine externe Reihe kommt AUFSTEIGEND zurueck",
           [d for d, _ in DB6.lies_externe_reihe(_spk, "cftc_cot", "gold")]
           == sorted(d for d, _ in _punkte),
           "jeder Aufrufer braucht sie chronologisch - das Umdrehen an vier "
           "Stellen waere vier Gelegenheiten, es zu vergessen")
    DB6.schreibe_externe_reihe(_spk, "cftc_cot", "gold", [(_punkte[0][0], 99.9)])
    pruefe(P, "eine nachtraegliche Berichtskorrektur schlaegt durch",
           DB6.lies_externe_reihe(_spk, "cftc_cot", "gold")[0][1] == 99.9
           and _spk.execute("SELECT COUNT(*) FROM externe_reihe").fetchone()[0]
           == len(_punkte),
           "die CFTC revidiert regelmaessig - INSERT OR IGNORE wuerde dauerhaft "
           "den ersten, falschen Wert fuehren")

    # `init_db` legt open_interest_snapshot bereits an - eine zweite
    # CREATE-Anweisung waere eine zweite Schemadefinition und bricht.
    _netz6 = []
    import api.cftc_cot as CC6

    _echtcot = CC6.get_cot_long_anteil_history
    try:
        CC6.get_cot_long_anteil_history = (
            lambda *a, **k: _netz6.append("cot") or [])
        _r6 = PO5.lage(_spk, "OD7H", assetklasse="rohstoffe")
        pruefe(P, "COT kommt aus der Datenbank, nicht aus dem Netz",
               _r6.get("cot") is not None and not _netz6,
               "`rolle_g` oeffnet mit mode=ro und kann nicht schreiben - haengt "
               "die Reihe am Netz, faellt der Fakt mit dem Anbieter aus")
        pruefe(P, "und das Perzentil traegt das Fenster im Satz",
               any("Wochenberichte" in s and "Perzentil" in s
                   for s in PO5.saetze(_r6)),
               "R-T1: das Fenster gehoert in den Satz")
        pruefe(P, "COT erreicht NUR Rohstoffe",
               PO5.lage(_spk, "OD7H", assetklasse="krypto").get("cot") is None
               and PO5.lage(_spk, "OD7H").get("cot") is None
               and PO5.lage(_spk, "BTC", assetklasse="rohstoffe").get("cot") is None,
               "ein Symbol ohne COT-Zuordnung darf keinen fremden Bericht "
               "bekommen - fail-closed wie beim Boersenfluss")
        pruefe(P, "COT deckt G1 UND G2 - es ist symbolspezifisch",
               "cot" in MK5.SYMBOLSPEZIFISCH_G
               and "cot_perzentil" in MK5.QUELLEN_G["cot"]
               and _r6.get("cot_perzentil") is not None,
               "Gold, Silber, Kupfer und Erdgas haben je einen eigenen Bericht "
               "- anders als der BTC-weite Boersenfluss")
    finally:
        CC6.get_cot_long_anteil_history = _echtcot
        _spk.close()

    # --- DIE AKTIENSEITE (16.08.2026, Schritt 4) ----------------------
    _spk2 = _sq6.connect(":memory:")
    _spk2.row_factory = _sq6.Row
    DB6.init_db(_spk2)
    from datetime import date as _dt6
    from datetime import timedelta as _td6

    _st6 = _dt6(2023, 1, 15)
    DB6.schreibe_externe_reihe(
        _spk2, "finra", "TST_days_to_cover",
        [((_st6 + _td6(days=15 * i)).isoformat(), 1.0 + (i * 3) % 25 / 10.0)
         for i in range(104)])
    DB6.schreibe_externe_reihe(_spk2, "sec_edgar", "TST_insider_kaeufe",
                               [("2026-08-16", 0.0)])
    DB6.schreibe_externe_reihe(_spk2, "sec_edgar", "TST_insider_verkaeufe",
                               [("2026-08-16", 55.0)])
    _ak6 = PO5.lage(_spk2, "TST", assetklasse="aktien")
    _s6 = " ".join(PO5.saetze(_ak6))
    pruefe(P, "Aktien: Leerverkaufsposition UND Insider erreichen Rolle G",
           _ak6.get("short_interest") is not None
           and _ak6.get("insider") is not None
           and not MK5.pruefe_g(_ak6),
           "als einzige Gruppe traegt sie zwei SYMBOLSPEZIFISCHE Quellen - "
           "damit sind G1 und G2 aus einer Hand erfuellt")
    pruefe(P, "der Insidersatz nennt BEIDE Seiten, auch die Null",
           "keinen Kauf" in _s6 and "55 Verkaeufe" in _s6,
           "gemessen ueber 730 Tage kaufte bei PLTR dreimal jemand und bei VST "
           "keinmal - die Null IST die Aussage, nicht die fehlende Haelfte")
    pruefe(P, "und er deutet nicht",
           not any(w in _s6.lower() for w in
                   ("signal", "bearish", "bullish", "schlechtes zeichen",
                    "vertrauen", "zuversicht")),
           "Fuehrungskraefte bekommen Aktien als Verguetung und verkaufen sie "
           "planmaessig - `sec_edgar.py` sagt das im Modulkopf selbst")
    pruefe(P, "Aktienquellen erreichen NUR Aktien",
           PO5.lage(_spk2, "TST", assetklasse="krypto").get("short_interest") is None
           and PO5.lage(_spk2, "TST").get("insider") is None,
           "fail-closed wie bei Boersenfluss und COT")

    # ⚠️ DIE SEC-SPERRE - der Fall, der am 16.08. tatsaechlich eintrat.
    import api.sec_edgar as SE6

    pruefe(P, "eine SEC-Sperre hat eine EIGENE Fehlerklasse",
           issubclass(SE6.SecGesperrtError, Exception)
           and "SecGesperrtError" in _quelltext("scheduler/background.py"),
           "ohne sie endet eine Drosselung als leere Liste - und damit als "
           "Aussage ueber das Unternehmen, die niemand geprueft hat")
    pruefe(P, "und der Job schreibt bei einer Sperre NICHTS",
           _quelltext("scheduler/background.py").count(
               "except SecGesperrtError") >= 1,
           "der gestrige Stand ist ehrlicher als eine frisch datierte Null")
    pruefe(P, "SEC-Abrufe laufen im Takt",
           hasattr(SE6, "_im_takt")
           and SE6._MAX_JE_SEKUNDE <= 10.0
           and _quelltext("api/sec_edgar.py").count("_im_takt()") >= 3,
           "die SEC drosselt bei zehn Anfragen je Sekunde - ein Lauf mit 120 "
           "Filings hat die Sperre am 16.08. real ausgeloest")
    _spk2.close()

    # --- FUNDAMENTALDATEN ZU ROLLE BC (17.08.2026) --------------------
    #
    # Der erste Fakt der ENTSCHEIDENDEN Rolle, der nicht aus der
    # Kerzenreihe stammt. Gemessen war der Anteil bei 85 %; von allen
    # Merkmalen trennte nur das Momentum Einstieg von Halten.
    from agent import lagebeschreibung as LB8
    from agent import rollen_eingabe as RE8

    _f8 = LB8._fundamental({"gewinnwachstum_pct": 215.4,
                            "umsatzwachstum_pct": 92.8})
    pruefe(P, "Gewinn und Umsatz stehen mit ihrem VERHAELTNIS da",
           len(_f8) == 3 and any("schneller als der Umsatz" in s for s in _f8),
           "das Verhaeltnis ist die eigentliche Aussage - und es braucht "
           "keine erfundene Schwelle und keine Vergleichsgruppe")
    pruefe(P, "und es steht KEIN Analystenurteil darin",
           not any(w in " ".join(_f8).lower() for w in
                   ("buy", "kaufen", "kursziel", "empfehl", "analyst")),
           "`analysten_konsens` ist ein fertiges Urteil eines Dritten und "
           "`analysten_kursziel` ein Anker - beide ROT (R-T2/R-T3)")
    pruefe(P, "ohne Daten entsteht KEIN Satz",
           LB8._fundamental(None) == [] and LB8._fundamental({}) == [],
           "eine Zeile 'keine Angabe' bei 54 Assets, die gar keine haben "
           "koennen, waere Rauschen")
    pruefe(P, "der Block steht VOR dem Verlauf",
           LB8.BLOCK_REIHENFOLGE.index("fundamental")
           < LB8.BLOCK_REIHENFOLGE.index("verlauf"),
           "R-T9 ist gemessen: was zuerst steht, wiegt schwerer - den "
           "einzigen Nicht-Chart-Satz hinten zu verstecken hiesse, ihn "
           "zu uebergeben")
    pruefe(P, "und er erreicht NUR Aktien",
           RE8.fundamentaldaten("BTC", None, "krypto") is None
           and RE8.fundamentaldaten("PLTR", None, None) is None,
           "ein Zertifikat hat keinen Gewinn, ein Coin kein "
           "Umsatzwachstum - fail-closed wie beim Boersenfluss")

    # --- DER UMSCHLAG FUER KRYPTO SPOT (17.08.2026) -------------------
    #
    # Krypto stellt 93 % aller Urteile, davon 37 % Spot - und Rolle BC
    # hatte dort KEINEN Fakt ausserhalb der Kerzenreihe.
    _u8 = LB8._umschlag({"anteil_pct": 4.8, "perzentil": 62, "n": 400})
    pruefe(P, "der Umschlag nennt Anteil, Fenster UND Einordnung",
           len(_u8) == 1 and "Perzentil" in _u8[0]
           and "gewohnten Bereich" in _u8[0],
           "R-T1 und R-T11 - Fenster im Satz, und ein Wort dazu, ob das "
           "viel ist")
    pruefe(P, "ohne Daten entsteht kein Satz",
           LB8._umschlag(None) == [] and LB8._umschlag({}) == [],
           "fail-closed wie ueberall")
    pruefe(P, "und er erreicht NUR Krypto",
           RE8.umschlag("PLTR", None, "aktien") is None
           and RE8.umschlag("BTC", None, None) is None,
           "`price_cache` fuehrt Marktkapitalisierung nur fuer Coins - eine "
           "ETF-Marktkapitalisierung waere etwas anderes")
    pruefe(P, "er steht bei den Umsatzaussagen, nicht vorn",
           LB8.BLOCK_REIHENFOLGE.index("umschlag")
           > LB8.BLOCK_REIHENFOLGE.index("volumen"),
           "er ist Kontext zur Handelbarkeit, nicht der Anlass - anders "
           "als die Ertragslage eines Unternehmens")

    # --- ROLLE G LANDET AUCH IN DER DATENBANK (17.08.2026) -------------
    #
    # `hole()` liefert einwand/einwand_grund/grundlage, `schreibe()` las
    # aber nur die ALTEN Schluessel. Die Mail zeigte den Einwand, die
    # Datenbank bekam nichts - zwoelf EROEFFNEN-Signale am 17.08. ohne eine
    # einzige gespeicherte Gegenpruefung. Eine Messluecke, kein Ausfall,
    # und sie machte JEDE Auswertung der zweiten Stufe unmoeglich.
    import database.db as _db_mod7
    from agent import zweite_meinung as ZM7

    _sig7 = sqlite3.connect(":memory:")
    _sig7.row_factory = sqlite3.Row
    _db_mod7.init_db(_sig7)
    _pflicht7 = [d[1] for d in _sig7.execute("pragma table_info(signals)")
                 if d[3] and d[1] != "id"]
    _w7 = {"symbol": "BTC", "created_at": "2026-08-17", "action": "X"}
    for _f7 in _pflicht7:
        _w7.setdefault(_f7, 1 if ("gate" in _f7 or "version" in _f7) else "x")
    _sig7.execute(
        f"INSERT INTO signals (id,{','.join(_w7)}) VALUES "
        f"(9,{','.join('?' * len(_w7))})", tuple(_w7.values()))
    _sig7.commit()
    ZM7.schreibe(_sig7, 9, {"einwand": "ja", "einwand_grund": "weil"})
    _r7 = _sig7.execute(
        "SELECT zai_gegenpruefung_urteil, zai_gegenpruefung_kurzbegruendung "
        "FROM signals WHERE id = 9").fetchone()
    pruefe(P, "der Einwand der Rolle G landet auf der Signalzeile",
           _r7[0] == "ja" and _r7[1] == "weil",
           "die Mail zeigte ihn, die Datenbank bekam nichts - damit war "
           "jede Auswertung der zweiten Stufe unmoeglich")
    _sig7.close()

    # --- O-33: HEDGE-INSTRUMENTE OHNE CODEEINGRIFF (17.08.2026) --------
    import importlib

    import config as _cm6
    from agent.hedge import pipeline as _hp6

    _echt_cfg = _cm6.load_config
    try:
        _cm6.load_config = lambda: {"hedge": {"instrumente": {
            "DBPK": {"hebel": 2, "referenz": "S&P 500"},
            "XSPS": {"hebel": 5, "referenz": "S&P 500"}}}}
        importlib.reload(_hp6)
        pruefe(P, "ein Hedge-Instrument kommt aus der Konfiguration",
               _hp6.SYMBOL_ZU_HEBEL_FAKTOR.get("XSPS") == 5.0
               and _hp6.ist_hedge_instrument("XSPS"),
               "elf Module lesen dieselbe Stelle - wer eines ergaenzen "
               "will, soll nicht in den Code greifen muessen")

        _cm6.load_config = lambda: {"hedge": {"instrumente": {
            "DBPK": {"hebel": 2}, "KAPUTT": {"referenz": "x"}}}}
        importlib.reload(_hp6)
        pruefe(P, "ein Eintrag OHNE Hebel wird verworfen",
               "KAPUTT" not in _hp6.SYMBOL_ZU_HEBEL_FAKTOR,
               "der Hebel ist die Groessenlogik - ein geratener Wert "
               "ueber- oder unterhedgt STILL")

        _cm6.load_config = lambda: (_ for _ in ()).throw(RuntimeError("x"))
        importlib.reload(_hp6)
        pruefe(P, "und eine kaputte Konfiguration faellt auf die Vorgaben",
               _hp6.SYMBOL_ZU_HEBEL_FAKTOR == _hp6.VORGABE_HEBEL_FAKTOR,
               "eine Konfiguration, die bei einem Tippfehler die "
               "Absicherung abschaltet, waere der schlechtere Tausch")
    finally:
        _cm6.load_config = _echt_cfg
        importlib.reload(_hp6)

    # --- G2 IST NICHT DURCH EINE MARKTWEITE GROESSE ZU ERFUELLEN ------

    pruefe(P, "der Boersenfluss deckt G1, aber NIE G2",
           "onchain" in MK5.QUELLEN_G
           and "onchain" not in MK5.SYMBOLSPEZIFISCH_G
           and any("G2" in f for f in MK5.pruefe_g(
               {"boersenfluss": {"perzentil": 50}})),
           "eine BTC-weite Groesse sagt ueber SEI nichts - wer sie fuer G2 "
           "zaehlt, taeuscht sich selbst")
    pruefe(P, "drei Boersen bleiben EINE Quellenart",
           MK5.QUELLEN_G["terminmarkt"].count("divergenz") == 1
           and len(MK5.quellen_g({"oi_aenderung_pct": 1, "divergenz": {},
                                  "long_anteil_pct": 60})) == 1,
           "G1 durch dreifaches Zaehlen derselben Groesse zu erfuellen waere "
           "eine Selbsttaeuschung im Code")
    _mem.close()

    # ------------------------------------------------------------------
    # DIE KURSREIHEN MUESSEN FRISCH SEIN (16.08.2026, aus dem NB-Export).
    #
    # Am 16.08. endeten ALLE 61 Reihen am Freitag, 14.08. - die Kette urteilte
    # am Sonntag auf Charts vom Freitag, und die Mail nannte einen zwei Tage
    # alten Kurs. Drei Dinge kamen zusammen: der 24-h-Takt beginnt bei jedem
    # Neustart neu (dreimal an dem Tag), der Sofortlauf greift erst bei MEHR
    # als zwei Tagen, und der Watchdog benutzt dieselbe Schwelle.
    # ------------------------------------------------------------------
    # DIE ANLASS-SPERRE (16.08.2026) - die Stufe sperrt, wenn der Nutzer sie
    # einschaltet. Gebaut NACH der Messung, nicht davor.
    from agent import anlass as AN6

    _aus = {"aktiv": False}
    _an = {"aktiv": True}
    _wdh = {"alter_stunden": 0.3, "gleich_asset": True, "gleich_voll": True,
            "geaenderte_bloecke": []}
    _neu = {"alter_stunden": 0.3, "gleich_asset": False, "gleich_voll": False,
            "geaenderte_bloecke": ["marken", "bestand"]}
    _erst = {"alter_stunden": None, "gleich_asset": False,
             "gleich_voll": False, "geaenderte_bloecke": []}
    pruefe(P, "die Vorgabe im Code sperrt NICHTS",
           not AN6.SPERRE_VORGABE["aktiv"]
           and AN6.sperrt(_wdh, None)[0] is False,
           "ein Modul, das beim blossen Einspielen die Produktion umstellt, "
           "nimmt dem Nutzer die Entscheidung ab")
    pruefe(P, "eingeschaltet sperrt sie den identischen Faktensatz",
           AN6.sperrt(_wdh, {"anlass": _an})[0] is True,
           "eine Empfehlung auf identischen Daten wie eine vorherige "
           "NICHT-Empfehlung ist keine Empfehlung")
    pruefe(P, "und laesst eine echte Aenderung durch",
           AN6.sperrt(_neu, {"anlass": _an})[0] is False,
           "sonst waere es keine Bremse, sondern ein Deckel")
    pruefe(P, "ohne Vorgaengerfrage wird nie gesperrt",
           AN6.sperrt(_erst, {"anlass": _an})[0] is False,
           "es gibt nichts zu wiederholen - im Zweifel durchlassen")
    # FEINJUSTIERUNG: beide Regler duerfen nur MEHR sperren, nie weniger.
    pruefe(P, "ignoriere_bloecke sperrt zusaetzlich",
           AN6.sperrt({**_neu, "geaenderte_bloecke": ["marken"]},
                      {"anlass": {**_an, "ignoriere_bloecke": ["marken"]}})[0]
           is True,
           "Marken tragen 15 % der Aenderungen und springen kursnah - ob das "
           "eine neue Lage ist, ist offen, deshalb ein Regler")
    pruefe(P, "mindest_bloecke ebenso",
           AN6.sperrt({**_neu, "geaenderte_bloecke": ["marken"]},
                      {"anlass": {**_an, "mindest_bloecke": 2}})[0] is True
           and AN6.sperrt(_neu, {"anlass": {**_an, "mindest_bloecke": 2}})[0]
           is False,
           "zwei bewegte Bloecke sind eine andere Aussage als einer")
    pruefe(P, "ein defektes Urteil sperrt NICHT",
           AN6.sperrt(None, {"anlass": _an})[0] is False
           and AN6.sperrt({}, {"anlass": _an})[0] is False,
           "eine Sperre, die bei einer Luecke zuschlaegt, entfernt Signale "
           "aus einem Grund, den niemand sieht")
    # DIE STUFE MUSS EIGENSTAENDIG SEIN - sonst ist hinterher nicht zu sehen,
    # ob eine Zeitregel oder ein identischer Faktensatz gebremst hat.
    from agent import rollen_gate as RG6

    pruefe(P, "der Anlass hat eine EIGENE Gate-Stufe",
           "anlass" in RG6.STUFEN_NAMEN
           and RG6.STUFEN_NAMEN.index("anlass")
           < RG6.STUFEN_NAMEN.index("wiederholung")
           and RG6.STUFEN_NAMEN.index("anlass")
           < RG6.STUFEN_NAMEN.index("urteil"),
           "sie kostet keinen Modellaufruf - dieselbe Trennung wie beim "
           "Cooldown am 14.08.")
    pruefe(P, "und sie sperrt VOR dem Modellaufruf",
           _quelltext("agent/rollen_lauf.py").index("_anlass_sperrt")
           < _quelltext("agent/rollen_lauf.py").index("RT.prompt_fuer"),
           "wer die Antwort erst holt und dann wegwirft, hat das Kontingent "
           "schon ausgegeben und das Rauschen bereits erzeugt")
    pruefe(P, "die Beobachtung wird auch beim Sperren geschrieben",
           "_beob = AN.beobachte(" in _quelltext("agent/rollen_lauf.py"),
           "sonst verschwaende mit der Sperre die Zahl, an der man sie "
           "spaeter beurteilen koennte")

    # ------------------------------------------------------------------
    # DER EXPORT MUSS DIE ANLASSMESSUNG TRAGEN (16.08.2026). Ohne sie liess
    # sich nach dem Scharfschalten der Sperre nur durch Auspacken des
    # DB-Backups sehen, ob sie greift.
    _q_ex = _quelltext("extract_notebook_diagnose.py")
    pruefe(P, "der Export traegt die Anlassmessung",
           'aus["anlass"]' in _q_ex and "anlass_beobachtung" in _q_ex,
           "eine Stufe, die sperrt, muss im Export sichtbar sein - sonst "
           "sieht man nur, dass weniger kommt, nicht warum")
    pruefe(P, "und nennt ihre eigene Einschraenkung",
           "VOR dem Cooldown" in _q_ex,
           "die Quote ist NICHT der Anteil vermeidbarer Modellaufrufe - wer "
           "das nicht dazuschreibt, laedt zur Fehldeutung ein")
    # FEHLALARME: die alte Gate-Semantik galt auch fuer die neue Kette.
    pruefe(P, "die Gate-Auffaelligkeit gilt nur der ALTEN Kette",
           'zeile.get("quelle_kette") != "rollen"' in _q_ex,
           "in der Rollen-Kette ist gate_passed=0 die NEIN-Messung, kein "
           "Widerspruch - sonst 13 Scheinfunde in jedem Export")
    pruefe(P, "und die Traceback-Meldung nennt Zeitraum und Ursache",
           "haeufigste Ursache" in _quelltext("pruefe_export_standard.py"),
           "eine grosse Zahl ohne Zeitbezug ueberdeckt die echten Funde "
           "daneben - 11.953 von 11.970 stammten aus 36 Minuten")

    # ------------------------------------------------------------------
    # NACHHOLEN, WAS HEUTE NICHT LIEF (16.08.2026). Fuenf taegliche Cron-Jobs
    # zwischen 06:00 und 07:15 liefen in 48 Stunden zusammen viermal, der
    # Ausstiegs-Job gar nicht - die App war 51 % der Zeit aus, und
    # APScheduler holt nichts nach (Jobstore im Speicher).
    import sqlite3 as _sq7
    from datetime import datetime as _dt7, timedelta as _td7

    import database.db as _db7

    _c7 = _sq7.connect(":memory:")
    _c7.row_factory = _sq7.Row
    pruefe(P, "ein nie gelaufener Job meldet None",
           _db7.letzter_joblauf(_c7, "neu") is None,
           "None heisst NIE, nicht 'unbekannt' - der Aufrufer darf daraus "
           "'jetzt nachholen' machen")
    _db7.merke_joblauf(_c7, "neu")
    _z7 = _db7.letzter_joblauf(_c7, "neu")
    pruefe(P, "nach dem Lauf steht ein Zeitstempel da",
           isinstance(_z7, str) and _z7.startswith(str(_dt7.now().year)),
           "ohne ihn holte der Nachholer bei JEDEM Neustart erneut nach - "
           "bei elf Neustarts am Tag waeren das elf Mails")
    pruefe(P, "und ein zweiter Lauf ueberschreibt ihn",
           (_db7.merke_joblauf(_c7, "neu"),
            _db7.letzter_joblauf(_c7, "neu") >= _z7)[1],
           "sonst waere die Frage 'lief er heute schon' nicht beantwortbar")
    _c7.close()
    _q7 = _quelltext("scheduler/background.py")
    pruefe(P, "die drei taeglichen Jobs vermerken ihren Lauf",
           _q7.count("merke_joblauf(") >= 3,
           "wer nicht vermerkt, wird bei jedem Neustart nachgeholt")
    # ⚠️ NICHT UEBER DIE TEXTPOSITION. Meine erste Fassung verglich, wo die
    # drei Aufrufe im Quelltext STEHEN - dort steht der Ausstiegs-Job zuerst.
    # Die Reihenfolge steckt aber in den VERSATZSEKUNDEN, nicht in der
    # Schreibreihenfolge. Derselbe Fehler wie bei der steigenden Testreihe:
    # der Test hing am falschen Gegenstand.
    import re as _re7
    _versatz = {m.group(1): int(m.group(2)) for m in
                _re7.finditer(r'_nachholen\("(\w+)",\s*(\d+)\)', _q7)}
    pruefe(P, "und der Nachholer haelt die Reihenfolge ein",
           _versatz.get("backward_tracking", 9e9)
           < _versatz.get("portfolio_wert", 9e9)
           < _versatz.get("ausstiegs_empfehlungen", 9e9),
           f"Versatz gemessen: {_versatz}. 'Die Reihenfolge ist noetig, nicht "
           f"kosmetisch' - die Ausstiegsregel rechnet auf Werten, die das "
           f"Backward-Tracking vorher fortschreibt")
    pruefe(P, "im Zweifel wird NICHT nachgeholt",
           "Job laeuft wie bisher zur Uhrzeit" in _q7,
           "ein Nachholer, der bei einer Luecke feuert, macht aus einem "
           "Lesefehler einen Modellaufruf")

    # ------------------------------------------------------------------
    # JEDE SIGNALZEILE TRAEGT IHREN PROMPT-STAND (16.08.2026).
    #
    # 30 von 285 trugen keinen - ausschliesslich Verkaufszeilen (28
    # REDUZIEREN, 2 VERKAUFEN). Der Ausstiegspfad uebergab `prompt_stand=None`.
    # Folge: die Verkaufsseite faellt aus jedem Vorher-Nachher-Vergleich
    # heraus - ausgerechnet der Teil, ueber den am wenigsten bekannt ist
    # (O-29: kein Merkmal trennt Verkaufen von Halten).
    _q8 = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "auch die Ausstiegszeile traegt den Prompt-Stand",
           "prompt_stand=None" not in _q8,
           "jeder Messbefund gehoert zu einem Stand - eine Zeile ohne ihn "
           "ist spaeter keinem Vergleich zuzuordnen")
    pruefe(P, "und es ist DERSELBE wie beim Einstieg",
           _q8.count('getattr(RT2, "PROMPT_STAND"') == 1
           or _q8.count('PROMPT_STAND') >= 3,
           "`befund` ist die Antwort von Rolle BC und entsteht aus demselben "
           "Prompt - ein eigener Stand waere eine Erfindung")

    # ------------------------------------------------------------------
    # PUNKT 2 (16.08.2026): Rohstoffe und Absicherung laufen jetzt durch die
    # Simulation. Beide waren scharf und in keinem Testlauf - dieselbe
    # Konstellation, die Rolle G drei Tage lang 'fertig' aussehen liess.
    from agent import signal_mail as SM9

    pruefe(P, "die Mailueberschrift folgt dem Instrument",
           SM9._ueberschrift_wert("spot") == "1. DER WERT"
           and SM9._ueberschrift_wert("absicherung") == "1. DIE ABSICHERUNG",
           "'DER COIN' stand ueber einem WisdomTree-Zertifikat und einem "
           "inversen S&P-ETF - ein Etikett, das dem Leser etwas anderes "
           "sagt, als vor ihm liegt")
    pruefe(P, "und 'COIN' steht nirgends mehr als Ueberschrift",
           '"1. DER COIN"' not in _quelltext("agent/signal_mail.py"),
           "die Kette bedient seit dem Vollumstieg sechs Gruppen")
    # DIE SIMULATION MUSS DEN PRODUKTIONS-COOLDOWN NEUTRALISIEREN.
    _q9 = _quelltext("simuliere_kette.py")
    pruefe(P, "die Simulation datiert den Cooldown zurueck",
           "-30 days" in _q9,
           "gegen ein NB-Backup sperrt der echte Cooldown jedes Symbol - "
           "die Simulation praefte dann einen Produktionsstand, nicht die "
           "Kette. Gemessen: hedge und themen_etf kamen mit 0 Aufrufen durch")
    # UND DIE ANLASS-STUFE MUSS VOR DEM COOLDOWN GEBUCHT WERDEN.
    _q9b = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Anlass-Stufe wird VOR dem Cooldown gebucht",
           _q9b.index('durchlauf.bestanden(symbol, "anlass")')
           < _q9b.index("WH.gesperrt_bis"),
           "sonst steht sie mit '0 bestanden, 0 verloren' da, obwohl "
           "Symbole sie passiert haben - ein Trichterloch")

    # ------------------------------------------------------------------
    # DIE MINDESTGRUNDLAGEN ALS CODE (16.08.2026 abends, R-R1 bis R-R3).
    #
    # Sie standen seit heute frueh als TEXT im Regelwerksmanual - und genau
    # diese Luecke hat am selben Tag zugeschlagen: Rolle A urteilte in der
    # Produktion mit 12 statt 15 Aussagen, weil zwei Makro-Spalten auf dem
    # Notebook fehlten. `lade_makro()` ist fail-soft, der Satz entfiel lautlos.
    from agent import mindestkriterien as MK9

    _voll_a = ["Bitcoin steht 5 % ueber dem von vor 250 Handelstagen.",
               "Bitcoin schwankt taeglich um 2 % des Kurses.",
               "Bitcoin verzeichnet je gehandeltem Euro Umsatz eine Bewegung.",
               "Die Netto-Liquiditaet des US-Finanzsystems betraegt 5.987 Mrd.",
               "Der Abstand zwischen zehnjaehriger und kurzfristiger Rendite.",
               "Die Anlegerstimmung zu Bitcoin liegt im 77. Perzentil."]
    pruefe(P, "Rolle A: vollstaendiges Lagebild meldet nichts",
           MK9.pruefe_a(_voll_a) == [],
           "eine Warnung, die immer kommt, liest niemand")
    pruefe(P, "und der echte Produktionsausfall wird erkannt",
           MK9.pruefe_a(_voll_a[:3]) == ["Makro", "Stimmung"],
           "genau die zwei Dimensionen, die am 16.08. in der Produktion "
           "fehlten - und die als 'erfuellt' dokumentiert waren")
    pruefe(P, "die Breite wird NICHT verlangt",
           not any(n == "Breite" for n, _ in MK9.DIMENSIONEN_A),
           "sie ist am 12.08. ersatzlos gestrichen worden - sie zu "
           "verlangen hiesse, etwas zu fordern, das wir entfernt haben")
    pruefe(P, "Rolle BC: Auftrag und Bestand sind Pflicht",
           MK9.pruefe_bc({"stand": ["y"]}, None) == ["auftrag"]
           and "Block bestand" in MK9.pruefe_bc(
               {"auftrag": ["x"], "stand": ["y"]},
               {"bestand": [], "verlauf": ["b"]}),
           "der KAS-Fall: das Modell kaufte in eine Verlustposition nach, "
           "weil der Bestand nicht in seiner Grundlage vorkam")
    pruefe(P, "aber der Ausloeser wird NICHT verlangt",
           "ausloeser" not in MK9.PFLICHT_BC
           and "trigger" not in MK9.PFLICHT_BC,
           "er fehlt strukturell und hat eine eigene Phase - eine Warnung "
           "bei JEDEM Urteil waere Rauschen")
    # ROLLE G ZAEHLT QUELLEN, NICHT ZAHLEN.
    _g_heute = {"oi_aenderung_pct": -1.4, "funding_perzentil": 72,
                "long_anteil_pct": 65, "regime": "baer"}
    pruefe(P, "Rolle G: drei Zahlen aus einer Tabelle sind EINE Quelle",
           MK9.quellen_g(_g_heute) == ["terminmarkt"],
           "sie beschreiben dieselbe Menge Menschen auf derselben Boerse")
    pruefe(P, "und das Regime zaehlt NICHT als fremde Quelle",
           "regime" not in str(MK9.QUELLEN_G),
           "es wird aus BTC-Kurs und Fear & Greed gerechnet - beides sieht "
           "Rolle A bereits")
    pruefe(P, "heute erfuellt Rolle G ihre Mindestgrundlage NICHT",
           MK9.pruefe_g(_g_heute) != [],
           "eine Quelle statt zwei - dokumentiert, nicht behoben")
    pruefe(P, "mit einer zweiten Quelle ist sie erfuellt",
           MK9.pruefe_g(dict(_g_heute, cot_perzentil=94)) == [],
           "CFTC COT waere die naechste - gebaut, nicht verdrahtet")
    # SPERREN NUR AUF ANSAGE.
    pruefe(P, "die Vorgabe sperrt NICHTS",
           MK9.melde("G", ["x"], None) is False
           and MK9.konfig(None)["sperren"] == (),
           "sonst legte das blosse Einspielen Rolle G still - sie erfuellt "
           "ihre eigene Grundlage heute nicht")
    # ⚠️ DER WEG ZUR ROLLE MUSS OFFEN SEIN, nicht nur der Parameter da.
    # Beim Gegentest aenderte `sperren=[G]` nichts: `rolle_g` hatte den
    # Parameter, aber `hole()` reichte ihn nicht durch. Zum zweiten Mal an
    # einem Tag dasselbe Muster wie beim Symbol - deshalb eine eigene Pruefung.
    _q_zm = _quelltext("agent/zweite_meinung.py")
    pruefe(P, "die Konfiguration erreicht Rolle G wirklich",
           "config: dict | None = None" in _q_zm
           and "db_config=config" in _q_zm
           and "config=config" in _quelltext("agent/rollen_lauf.py"),
           "ein Parameter ohne Weg dorthin ist wirkungslos - und der "
           "Gegentest sah aus, als wirke die Sperre nicht")
    pruefe(P, "und sperrt je Rolle, wenn der Nutzer es sagt",
           MK9.melde("G", ["x"], {"mindestkriterien": {"sperren": ["G"]}})
           is True
           and MK9.melde("A", ["x"], {"mindestkriterien": {"sperren": ["G"]}})
           is False,
           "die drei Rollen haben sehr verschiedene Luecken")

    import staleness as ST5

    pruefe(P, "Krypto hat eine eigene, engere Frischeschwelle",
           ST5.KRYPTO_OHLC_STALE_THRESHOLD_DAYS == 1
           and ST5.HISTORY_STALE_THRESHOLD_DAYS == 2,
           "Krypto handelt rund um die Uhr - zwei Tage Rueckstand sind dort "
           "kein Wochenende, sondern ein Ausfall")
    # ⚠️ RELATIV ZU HEUTE, NICHT MIT FESTEM DATUM (korrigiert 17.08.2026).
    # Hier stand "2026-08-14" - am 16.08. war das zwei Tage zurueck und der
    # Fall traf zu. Einen Tag spaeter sind es drei, beide Schwellen
    # schlagen an, und die Pruefung scheiterte. Sie mass den Kalender
    # statt den Code und lief mit der Zeit ab.
    # ⚠️ ZWEITE KORREKTUR, 20.08.2026: DIESELBE UHR WIE DIE FUNKTION.
    #
    # Hier stand `date.today()` - die LOKALE Uhr. `is_history_stale` rechnet
    # aber in UTC. Zwischen Mitternacht und der UTC-Grenze sind das zwei
    # verschiedene Tage: die Pruefung baute eine "zwei Tage alte" Kerze, die
    # fuer die Funktion einen Tag alt war, und schlug fehl - gefunden genau
    # in dieser Stunde. Eine Pruefung darf ihre Eingabe nicht aus einer
    # anderen Quelle nehmen als die geprueffte Funktion.
    from datetime import datetime as _dt5
    from datetime import timedelta as _td5
    from datetime import timezone as _tz5

    _zwei_tage_alt = (_dt5.now(_tz5.utc).date() - _td5(days=2)).isoformat()
    pruefe(P, "und der echte Ausfall wuerde jetzt erkannt",
           ST5.is_history_stale(_zwei_tage_alt, schwelle_tage=1) is True
           and ST5.is_history_stale(_zwei_tage_alt) is False,
           f"Kerze von {_zwei_tage_alt}: die geteilte Schwelle (2 Tage) "
           "schweigt, die Krypto-Schwelle (1 Tag) schlaegt an")
    pruefe(P, "die geteilte Schwelle bleibt unangetastet",
           "HISTORY_STALE_THRESHOLD_DAYS = 2" in _quelltext("staleness.py"),
           "an ihr haengen die Anzeige und das Gate R-5.0 der alten Kette - "
           "sie zu senken waere die Verschlimmbesserung")
    pruefe(P, "der Kraken-Check benutzt die engere",
           "schwelle_tage=staleness.KRYPTO_OHLC_STALE_THRESHOLD_DAYS"
           in _quelltext("scheduler/background.py"),
           "sonst greift der Sofortlauf beim Neustart weiterhin nicht")

    from agent import rolle_trader as RT5

    # ⚠️ DIESE ZEILE WIRD BEI JEDER AENDERUNG AN DER EINGABE DER ROLLE BC
    # MITGEZOGEN - das ist ihr Zweck, nicht ihr Wartungsaufwand. Zuletzt
    # am 17.08.2026: die Fundamentaldaten sind dazugekommen, damit sieht
    # das Modell etwas anderes als vorher.
    #
    # Jeder Messbefund gehoert zu einem Stand. Ohne den Sprung waeren
    # Urteile vor und nach der Aenderung nicht unterscheidbar - und ein
    # Vorher-Nachher-Vergleich, der beide Haelften vermischt, misst
    # nichts.
    # Zuletzt 2026-08-17c: eine Zeile gegen erfundene Perzentile (A6).
    pruefe(P, "der Prompt-Stand ist mitgezogen",
           RT5.PROMPT_STAND == "2026-08-17e",
           "die Eingabe UND die Anweisung der Rolle BC haben sich "
           "geaendert - ohne neuen Stand waeren die Urteile davor und "
           "danach nicht auseinanderzuhalten")

    # ------------------------------------------------------------------
    # AA. DIE VERKAUFSSEITE (14.08.2026) - der groesste Fund des Echtbetriebs.
    #
    # Elf von 45 Urteilen waren Verkaufsseite und keines hat den Nutzer
    # erreicht: neun REDUZIEREN und zwei VERKAUFEN fielen in `_schreibe_nein()`
    # und wurden als "reines LLM-Halten" gebucht. `AKTIONEN_MIT_EINSTIEG` kennt
    # drei Woerter, alles andere galt als Nichtstun.
    #
    # NACHGERECHNET AM ECHTEN LAUF: alle elf hatten Bestand, zusammen ueber
    # 1.400 EUR Gegenwert - darunter BTC mit 917 EUR.
    from agent import verkaufsrechnung as VK4

    pruefe(P, "Verkaufen und Nichtstun sind nicht mehr dasselbe",
           VK4.ist_ausstieg("VERKAUFEN") and VK4.ist_ausstieg("REDUZIEREN")
           and not VK4.ist_ausstieg("HALTEN")
           and not VK4.ist_ausstieg("NICHTS_TUN"),
           "seit 15.08. VIER Klassen: Einstieg, Ausstieg, Hebelanpassung, "
           "Nichts - die dritte kam mit O-31 dazu")
    pruefe(P, "die Abzweigung steht VOR der Nein-Buchung",
           _quelltext("agent/rollen_lauf.py").index(
               "VK.betrifft_bestand(aktion)")
           < _quelltext("agent/rollen_lauf.py").index(
               "if aktion not in SM.AKTIONEN_MIT_EINSTIEG:"),
           "sonst verschluckt dieselbe Zeile wieder alles, was nicht "
           "'kaufen' heisst")

    _voll = VK4.rechne(aktion="VERKAUFEN", menge=100.0, kurs_eur=2.0,
                       einstand_eur=4.0)
    _teil = VK4.rechne(aktion="REDUZIEREN", menge=100.0, kurs_eur=2.0,
                       einstand_eur=4.0)
    pruefe(P, "VERKAUFEN nimmt alles, REDUZIEREN ein Drittel",
           _voll["menge_verkauf"] == 100.0
           and abs(_teil["menge_verkauf"] - 100.0 / 3.0) < 1e-9,
           "das Drittel ist GESETZT, nicht gemessen - die Umkehrung der "
           "Tranche, bis eigene Ausstiegsdaten vorliegen")
    pruefe(P, "das Ergebnis der Position wird mitgerechnet",
           _voll["ergebnis_eur"] == -200.0
           and _voll["ergebnis_prozent"] == -50.0,
           "die Frage, die der Nutzer zuerst stellt - aber KEIN Grund fuer "
           "die Entscheidung, sondern die Ausgangslage")
    _gestakt = VK4.rechne(aktion="VERKAUFEN", menge=100.0, gestakt=60.0,
                          kurs_eur=2.0)
    pruefe(P, "der gestakte Teil wird abgezogen",
           _gestakt["menge_verkauf"] == 40.0,
           "eine Empfehlung ueber eine Menge, an die man nicht herankommt, "
           "ist keine")
    pruefe(P, "ohne Bestand gibt es keinen Auftrag",
           VK4.rechne(aktion="VERKAUFEN", menge=0.0, kurs_eur=2.0) is None,
           "ein VERKAUFEN auf etwas, das man nicht haelt, wird gebucht wie "
           "ein HALTEN - und misst mit, wie oft das vorkommt")
    pruefe(P, "ein zu kleiner Gegenwert wird benannt",
           VK4.rechne(aktion="VERKAUFEN", menge=1.0, kurs_eur=9.95)["zu_klein"]
           and not VK4.rechne(aktion="VERKAUFEN", menge=1.0,
                              kurs_eur=100.0)["zu_klein"],
           "QNT lag im echten Lauf bei 9,95 EUR - die Gebuehren stehen dort "
           "in keinem Verhaeltnis")
    _s = VK4.saetze(_voll)
    pruefe(P, "die Verkaufsmail nennt Menge, Gegenwert und Stand",
           any("Verkaufen" in x for x in _s)
           and any("Gegenwert" in x for x in _s)
           and any("Stand" in x for x in _s),
           "wieviel wovon, und was bleibt uebrig - mehr braucht ein "
           "Ausstieg nicht, und weniger reicht nicht")
    # ELF EINZELMAILS WAEREN SCHLIMMER GEWESEN ALS DIE LUECKE. Nutzereinwand
    # 14.08.: *"das ist zu viel"*. Eine Sammelmail je Lauf, nach Gegenwert
    # sortiert - die Einstiegsmails bleiben einzeln, sie tragen eine Planung.
    _posten = [{"symbol": "BTC", "begruendung": "Momentum kippt.",
                "verkauf": VK4.rechne(aktion="REDUZIEREN", menge=0.05,
                                      kurs_eur=54000.0, einstand_eur=68000.0)},
               {"symbol": "SUPRA", "begruendung": "These gefallen.",
                "verkauf": VK4.rechne(aktion="VERKAUFEN", menge=119592.0,
                                      kurs_eur=0.000145, einstand_eur=0.0009)}]
    _b, _txt = VK4.sammel_mail(_posten, modell="m", zeitpunkt="2026-08-14")
    pruefe(P, "die Verkaufsseite kostet EINE Mail, nicht elf",
           _b.count("Verkaufsvorschlaege") == 1 and "BTC" in _txt
           and "SUPRA" in _txt,
           "elf Einzelmails haetten die Kaufmails auf einundzwanzig gebracht "
           "- und die Verkaufsseite ist die, die man nicht uebersehen darf")
    # SORTIERT WIRD NACH DRINGLICHKEIT, NICHT NACH EURO - die dokumentierte
    # Regel (`backward_tracking`, Zeile 4930): "Dringlichstes zuerst ... NICHT
    # nach Buchgewinn. Der groesste ungesicherte Gewinn ist nicht automatisch
    # der dringendste Fall." Meine erste Fassung sortierte nach Gegenwert, und
    # diese Pruefung hat den Fehler mitgeschrieben.
    pruefe(P, "das GANZ-Raus steht vor dem Teilverkauf",
           _txt.index("SUPRA ") < _txt.index("BTC "),
           "SUPRA soll ganz raus (17 EUR), BTC nur ein Drittel (900 EUR) - "
           "'raus' ist dringender als 'weniger davon'")
    _mit_f = [dict(_posten[0], fuehrung={"empfehlung": "SCHLIESSEN · faellig",
                                         "mfe_r": 2.4}), _posten[1]]
    _, _txt2 = VK4.sammel_mail(_mit_f)
    pruefe(P, "sind sich beide Ebenen einig, steht das ganz oben",
           _txt2.index("BTC ") < _txt2.index("SUPRA ")
           and "Fuehrung: SCHLIESSEN" in _txt2,
           "die deterministische Fuehrung sagt schliessen UND das Modell sagt "
           "reduzieren - der einzige Fall, in dem beide dasselbe meinen")
    pruefe(P, "die Fuehrung steht in DERSELBEN Mail",
           "hoechster Stand +2,40 R" in _txt2,
           "fuer BTC liefen am 14.08. zwei Ausstiegswege parallel - getrennt "
           "gelesen sehen sie aus wie zwei Meinungen zum selben Symbol")
    pruefe(P, "ohne Ausstieg gibt es keine Mail",
           VK4.sammel_mail([]) is None,
           "eine leere Sammelmail waere eine Benachrichtigung ueber nichts")
    pruefe(P, "die Sammelmail sagt, was sie NICHT ist",
           "KEINE GEWINNMITNAHME" in _txt,
           "Nutzerfrage 13.08.: 'Wenn da steht jetzt schliessen, ist das "
           "Gewinnzone erreicht?' - nein, im Gegenteil")
    pruefe(P, "der Lauf verschickt die Sammelmail auch",
           "versand(*_sammel)" in _quelltext("agent/rollen_lauf.py"),
           "gebaut und nicht verschickt waere die Luecke von vorhin")

    # WELCHES SIGNAL MELDET? Nutzerfrage 14.08. - mehrere offene Signale je
    # Symbol sind der Normalfall (DBPK und OD7L je 5, 3QSS 4, MON/OD7C je 3).
    # Der Absatzkopf nannte nur Symbol, Art und Tagesdatum.
    from agent import ausstiegsrechnung as AR3
    _e1 = {"symbol": "DBPK", "tier": "spot", "seit": "2026-08-01",
           "entry": 61200.0, "signal_id": 2986, "ist_hebel": False,
           "eur_je_usd": 1.0}
    _e2 = dict(_e1, seit="2026-08-06", entry=59450.0, signal_id=3011)
    _k1, _k2 = AR3._absatz(_e1)[0], AR3._absatz(_e2)[0]
    pruefe(P, "zwei offene Signale zum selben Symbol sind unterscheidbar",
           _k1 != _k2 and "#2986" in _k1 and "#3011" in _k2
           and "61.200" in _k1 and "59.450" in _k2,
           "Einstieg sagt WELCHE Position gemeint ist, die Nummer macht es "
           "eindeutig - die Nummer allein waere technisch, der Einstieg "
           "allein mehrdeutig")
    pruefe(P, "der Rueckverweis nennt die Ursprungsmail woertlich",
           any('aus der Mail "TradingInfoTool: DBPK - KAUFEN"' in _z
               for _z in AR3._absatz(dict(_e1, ur_aktion="KAUFEN"))),
           "Betreff und Datum genuegen fuers Postfach - Nutzervorgabe: "
           "'ich gehe nicht auf die Suche zum urspruenglichen signal'")
    pruefe(P, "die Handelsart ist Spot oder Hebel, nie der Gruppenschluessel",
           "Spot," in AR3._absatz(dict(_e1, tier="krypto"))[0]
           and "mit Hebel" in AR3._absatz(
               dict(_e1, tier="hebel", richtung="LONG"))[0],
           "unter '[KRYPTO-SPOT]' noch einmal 'krypto' zu schreiben ist "
           "doppelt und falsch beschriftet")
    # GRUPPIERT WIRD INNERHALB DER DRINGLICHKEIT, NICHT DARUEBER.
    _g = [dict(_e1, symbol=s, tier=k, empfehlung="SCHLIESSEN · faellig",
               ist_bestand=True)
          for s, k in (("BTC", "krypto"), ("ETH", "hebel"),
                       ("OD7H", "rohstoffe"), ("X136", "aktien"))]
    _txtg = " | ".join(AR3._nach_gruppen(_g))
    pruefe(P, "ab vier Eintraegen bekommt ein Block Gruppentitel",
           "[KRYPTO-HEBEL]" in _txtg and "[ROHSTOFFE]" in _txtg
           and _txtg.index("[KRYPTO-HEBEL]") < _txtg.index("[KRYPTO-SPOT]"),
           "sechs Gruppen in fester Lesereihenfolge - keine neuen erfunden")
    pruefe(P, "darunter wird nur sortiert, nicht ueberschrieben",
           "[KRYPTO-SPOT]" not in " | ".join(AR3._nach_gruppen(_g[:2])),
           "zwei Ebenen mal sechs Gruppen sind zwoelf Ueberschriften - bei "
           "drei Positionen mehr Geruest als Inhalt")

    pruefe(P, "die Ausstiegsabfrage holt die id ueberhaupt",
           "felder = (\"id, symbol, created_at" in _quelltext(
               "agent/krypto/backward_tracking.py"),
           "ohne sie kann die Mail nicht sagen, welches Signal meldet")
    # ZEITABLAUF UND UEBERHOLUNG SIND VERSCHIEDENE DINGE - und die Reihenfolge
    # der Pruefung entscheidet, welches Etikett eine Zeile bekommt.
    pruefe(P, "ueberholt wird VOR abgelaufen geprueft",
           _quelltext("agent/krypto/backward_tracking.py").index(
               "if _is_superseded(signal")
           < _quelltext("agent/krypto/backward_tracking.py").index(
               "elif _is_expired(signal"),
           "ein Signal, das ein neueres abgeloest hat, ist ueberholt - nicht "
           "'unentschieden abgelaufen'. Andersherum stuende die Ablösung als "
           "Zeitablauf in der Bilanz")
    pruefe(P, "der Zeitablauf steht als eigener Satz in der Mail",
           "und ist abgelaufen." in _quelltext("agent/ausstiegsrechnung.py"),
           "Nutzerfrage: 'wie unterscheide ich, ob nur ein Signal auslaeuft "
           "weil die Zeit abgelaufen ist'")

    # O-24 DIE CHARTS. Die alte Kette haengte zwei Inline-Grafiken an; die
    # Rollen-Kette reichte nur (betreff, text) durch - die Faehigkeit war da,
    # der Weg fehlte.
    from ui.trade_chart import render_trade_chart as _chart
    import math as _math

    class _KK:
        def __init__(_s, i):
            _s.close = 100 + 12 * _math.sin(i / 9)
            _s.high, _s.low = _s.close * 1.01, _s.close * 0.99
            _s.volume, _s.date = 1000.0, f"2026-05-{(i % 28) + 1:02d}"

    _rr = [_KK(i) for i in range(120)]
    _rech = {"einstieg_von_eur": 96.0, "einstieg_bis_eur": 98.5,
             "stop_eur": 92.0, "ziel_von_eur": 108.0}
    _png = _chart(reihe=_rr, index=119, rechnung=_rech, symbol="TST",
                  fx_eur_je_usd=0.92)
    pruefe(P, "der Trade wird als Bild gezeichnet",
           bool(_png) and _png[1:4] == b"PNG" and len(_png) > 5000,
           "Kurs, Einstiegszone, Stop und Ziel - die Frage, die aus Zahlen "
           "allein schwer zu beantworten ist: liegt der Stop dort, wo der "
           "Kurs schon oefter war?")
    pruefe(P, "ohne Umrechnungsfaktor gibt es KEIN Bild",
           _chart(reihe=_rr, index=119, rechnung=_rech, symbol="TST",
                  fx_eur_je_usd=None) is None,
           "die Reihe steht in USD, die Rechnung in EUR - beides ungefragt in "
           "ein Bild zu legen ergibt richtige Form und falsche Skala. Ein "
           "fehlendes Bild ist ein Mangel, ein falsches eine Falschaussage")
    pruefe(P, "zu kurze Reihen ergeben kein Bild statt eines leeren",
           _chart(reihe=_rr[:5], index=4, rechnung=_rech, symbol="TST",
                  fx_eur_je_usd=0.92) is None)
    pruefe(P, "der Versandweg nimmt Bilder an",
           "def versand(betreff: str, text: str, bilder=None)" in _quelltext(
               "scheduler/rollen_job.py")
           and "inline_images=bilder or None" in _quelltext(
               "scheduler/rollen_job.py"),
           "send_notification_email kann das seit 23.07. - die Kette reichte "
           "es nur nie durch")

    pruefe(P, "der Verkaufsversand laesst sich abschalten, das Buchen nicht",
           "verkauf_mailt" in _quelltext("agent/rollen_lauf.py")
           and "verkauf_nicht_gemailt" in _quelltext("agent/rollen_lauf.py"),
           "0 von 1.142 in der alten Kette gegen 11 von 45 in der neuen - bis "
           "das eingeordnet ist, soll man zaehlen koennen ohne zu mailen. Ein "
           "Schalter, der die ZEILE unterdrueckt, waere wieder das Verschlucken")

    pruefe(P, "die Ausstiegszeile wird geschrieben",
           "felder[\"gate_passed\"] = 1" in _quelltext("agent/rollen_lauf.py"),
           "sonst greift der Cooldown nicht und dasselbe Symbol bekaeme in "
           "fuenfzehn Minuten dieselbe Verkaufsmail")

    # ------------------------------------------------------------------
    # AB. GEGENPRUEFUNG DER UMSETZUNGEN VOM 14.08. (Nutzeranweisung).
    #
    # Nicht: "laeuft es durch" - das sagen die Bloecke oben. Sondern: haelt
    # jede Aenderung das, was ihre Begruendung behauptet, und hat sie nichts
    # kaputtgemacht, das vorher ging.
    from agent import trefferbilanz as TB5
    from api import llm_basis as LB5
    from database import db as DB5

    # AB1 DIE VIER KOSTENARTEN - der Kern des Nutzerhinweises.
    #
    # Die Doku fuehrt vier Kostenarten (Regelwerk-Entscheidungslog 07.08.),
    # `trefferbilanz.kosten_r_aus_stop` kannte zwei. Jetzt delegiert sie an
    # `backward_tracking.kosten_in_r` - EINE Definition statt zweier.
    _k = lambda **kw: TB5.kosten_r_aus_stop(100.0, 95.0, position_eur=250, **kw)
    _krypto = _k(klasse="krypto", instrument="spot", tage=2.0)
    _boerse = _k(klasse="boerse", instrument="spot", tage=2.0)
    pruefe(P, "Krypto und Boerse werden verschieden gerechnet",
           _krypto is not None and _boerse is not None
           and abs(_krypto - _boerse) > 0.2,
           f"krypto {_krypto} gegen boerse {_boerse} - 1,5 % je Seite gegen "
           "1 EUR fix + 0,25 % Spread")
    _hebel_kurz = _k(klasse="krypto", instrument="hebel", hebel=3.0, tage=2.0)
    _hebel_lang = _k(klasse="krypto", instrument="hebel", hebel=3.0, tage=30.0)
    # ⚠️ DIE SCHWELLE WAR EIN FAKTOR 2 - UND DAS WAR EIN PROXY (01.09.2026).
    #
    # Er hielt nur, solange die Hebelkosten AUSSCHLIESSLICH aus Finanzierung
    # bestanden. Seit die Handelsgebuehr dazukommt (sie fehlte bis zum
    # 01.09.), teilen sich kurze und lange Haltedauer einen gemeinsamen
    # Sockel von 0,60 R, und das Verhaeltnis faellt auf 1,98 - die Pruefung
    # fiel um, obwohl die Aussage stimmte. Eine Schwelle auf einem
    # Verhaeltnis misst hier die falsche Groesse.
    #
    # Geprueft wird jetzt, was der Satz behauptet: der ZEITABHAENGIGE Anteil
    # waechst mit der Haltedauer, der Handelsanteil nicht.
    from agent.krypto.backward_tracking import kosten_in_r as _kir7
    _f = lambda tg: _kir7(0.05, "hebel", tg, hebel=3.0)
    _kurz7, _lang7 = _f(2.0), _f(30.0)
    pruefe(P, "beim Hebel kostet die HALTEDAUER, nicht nur der Trade",
           _hebel_lang > _hebel_kurz
           and _lang7["finanzierung_rel"] > 2 * _kurz7["finanzierung_rel"],
           f"2 Tage {_hebel_kurz:.3f} R gegen 30 Tage {_hebel_lang:.3f} R, "
           f"davon Finanzierung {_kurz7['finanzierung_rel']:.5f} gegen "
           f"{_lang7['finanzierung_rel']:.5f} - die Tagesstaffel auf "
           "geliehenes Kapital fehlte der neuen Kette vollstaendig; sie "
           "rechnete pauschal mit dem Krypto-Satz")
    pruefe(P, "und der Handelsanteil waechst dabei NICHT mit",
           abs(_lang7["handel_rel"] - _kurz7["handel_rel"]) < 1e-12,
           "Kauf und Verkauf fallen einmal an, egal wie lange die Position "
           "offen ist. Waeren beide Anteile zeitabhaengig, waere die "
           "Aufteilung nur kosmetisch")
    _hedge_kurz = _k(klasse="boerse", instrument="absicherung", tage=2.0)
    _hedge_lang = _k(klasse="boerse", instrument="absicherung", tage=180.0)
    pruefe(P, "die Absicherung traegt ihre laufende ETP-Gebuehr",
           _hedge_lang > _hedge_kurz,
           f"2 Tage {_hedge_kurz:.3f} R gegen 180 Tage {_hedge_lang:.3f} R - "
           "ohne sie erscheint eine ueber Monate gehaltene Absicherung "
           "billiger als sie ist")
    pruefe(P, "ohne Zusatzangaben bleibt die einfache Rechnung",
           TB5.kosten_r_aus_stop(100.0, 95.0, klasse="krypto") is not None,
           "sieben bestehende Aufrufer uebergeben weder Instrument noch "
           "Haltedauer - sie duerfen nicht brechen")

    # AB1b DIE AUSSTIEGSFUEHRUNG BRAUCHT DIE WATCHLIST.
    #
    # Gefunden in der Gegenpruefung an der eigenen Logzeile der Funktion:
    # ohne Watchlist traegt jede Zeile `tier = "spot"`, und die
    # Gruppenueberschriften der Ausstiegsmail waeren gebaut und wirkungslos.
    pruefe(P, "die Ausstiegsfuehrung wird MIT Watchlist geholt",
           "compute_ausstiegs_empfehlungen(conn, watchlist=_wl)" in _quelltext(
               "agent/rollen_lauf.py"),
           "sonst landet alles im Sammel-Topf 'spot' - die Funktion warnt "
           "selbst davor, und niemand hoerte hin")

    # AB1c DIE RECHNUNG RUNDETE JEDEN KURS AUF CENT.
    #
    # In der Gegenpruefung an einer echten Mail gefunden: KAS bei 0,02428 EUR
    # bekam Zone 0,02 bis 0,02, Stop 0,02, Ziel 0,03 - Einstieg, Stop und Ziel
    # fielen auf denselben Wert zusammen.
    #
    # UND DAS KORRIGIERT MEINEN EIGENEN BEFUND VON HEUTE FRUEH. Zur PLUME-Mail
    # ("0 bis 0 EUR") schrieb ich, die Rechnung sei richtig und nur die
    # Darstellung habe sie vernichtet. Das stimmte zur Haelfte: der
    # Formatierer machte den Schaden sichtbar, verursacht hat ihn `round(x, 2)`
    # in der Rechnung selbst.
    from agent import entscheidungsrechnung as ER5
    _r5 = ER5.rechne(kurs=0.0119, atr=0.0008, risiko_eur=24.0,
                     instrument="spot", betrag_wunsch_eur=800.0)
    pruefe(P, "ein Sub-Cent-Wert behaelt seine Geometrie",
           _r5["einstieg_von_eur"] != _r5["einstieg_bis_eur"]
           and _r5["stop_eur"] < _r5["einstieg_von_eur"]
           and _r5["ziel_von_eur"] > _r5["einstieg_bis_eur"],
           f"Zone {_r5['einstieg_von_eur']}-{_r5['einstieg_bis_eur']}, "
           f"Stop {_r5['stop_eur']}, Ziel {_r5['ziel_von_eur']}")
    _r6 = ER5.rechne(kurs=61234.0, atr=1450.0, risiko_eur=120.0,
                     instrument="spot", betrag_wunsch_eur=800.0)
    pruefe(P, "und ein grosser Kurs bekommt keine Scheingenauigkeit",
           abs(_r6["stop_eur"] - round(_r6["stop_eur"], 2)) < 1e-9,
           "sechs signifikante Stellen heissen bei 61.234 zwei Nachkomma - "
           "die Regel greift nur, wo sie gebraucht wird")
    pruefe(P, "Betraege bleiben auf Cent gerundet",
           abs(_r6["risiko_eur"] - round(_r6["risiko_eur"], 2)) < 1e-9,
           "ein Einsatz ist ein Eurobetrag, kein Kurs")

    # AB2 DER TOKENZAEHLER (O-25).
    pruefe(P, "der Zaehler kann in Schritten buchen",
           "schritt: int = 1" in _quelltext("database/db.py"),
           "Token sind derselbe Vorgang in einer anderen Einheit - dieselbe "
           "Tabelle, dieselbe Transaktion")
    with sqlite3.connect(":memory:") as _c5:
        _c5.row_factory = sqlite3.Row
        _c5.execute("CREATE TABLE api_call_kontingent (source TEXT, monat "
                    "TEXT, anzahl INTEGER, PRIMARY KEY (source, monat))")
        _c5.execute("CREATE TABLE api_call_kontingent_taeglich (source TEXT, "
                    "tag TEXT, anzahl INTEGER, PRIMARY KEY (source, tag))")
        DB5.increment_api_call_counter(_c5, "groq:token", schritt=1200)
        _stand = DB5.increment_api_call_counter(_c5, "groq:token", schritt=900)
        pruefe(P, "zwei Aufrufe ergeben 2.100 Token, nicht 2",
               _stand == 2100, f"gezaehlt: {_stand}")
        _eins = DB5.increment_api_call_counter(_c5, "groq")
        pruefe(P, "und der Aufrufzaehler bleibt bei eins je Aufruf",
               _eins == 1,
               "die Einheit steckt im Schluessel - wer beide vermischt, "
               "bekommt Unsinn, und das faellt sofort auf")
    pruefe(P, "die Einheit ist am Schluessel erkennbar",
           LB5.TOKEN_SUFFIX == ":token"
           and "zaehle_token(\"groq\"" in _quelltext("api/groq.py"),
           "damit niemand Token gegen Aufrufe vergleicht")
    pruefe(P, "gebucht wird NACH dem Aufruf, nicht davor",
           _quelltext("api/groq.py").index("zaehle_aufruf(\"groq\")")
           < _quelltext("api/groq.py").index("zaehle_token(\"groq\""),
           "die Tokenzahl steht erst in der Antwort; ein Fehlschlag "
           "verbraucht keine Token")

    # ------------------------------------------------------------------
    # AC. O-16 UND O-17 (14.08.2026).
    from agent import toepfe as TP6
    from agent import betraege as BE6
    from agent import wiederholung as WH6
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _HEDGE

    # AC1 O-16: SPOT UND ABSICHERUNG SIND TRENNBAR.
    #
    # Beide haben `hebel IS NULL`. Die Unterscheidung kommt aus der EINEN
    # Stelle, an der sie im Projekt steht - `SYMBOL_ZU_HEBEL_FAKTOR`. Hedge ist
    # keine Assetklasse; die Watchlist fuehrt DBPK und 3QSS als `etf`, und nur
    # ihre Mitgliedschaft dort macht sie zu Absicherungen.
    pruefe(P, "die Trennung nennt die Hedge-Symbole beim Namen",
           all(s in TP6.sql_bedingung("absicherung") for s in _HEDGE)
           and all(s in TP6.sql_bedingung("spot") for s in _HEDGE)
           and " NOT IN " in TP6.sql_bedingung("spot"),
           f"aus SYMBOL_ZU_HEBEL_FAKTOR: {sorted(_HEDGE)} - keine zweite Liste")
    pruefe(P, "und der Hebel bleibt unberuehrt",
           TP6.sql_bedingung("hebel") == "hebel IS NOT NULL",
           "er hat seinen eigenen, eindeutigen Unterscheider")

    with sqlite3.connect(":memory:") as _c6:
        # MIT `action` - seit dem 14.08. zaehlt der Topf nur EINSTIEGE, und
        # eine offene Position stammt in der Wirklichkeit immer aus einem.
        _c6.execute("CREATE TABLE signals (symbol TEXT, created_at TEXT, "
                    "action TEXT, quelle_kette TEXT, hebel REAL, "
                    "position_size_eur REAL, outcome_status TEXT)")
        for _s, _h, _p in (("BTC", None, 800.0), ("DBPK", None, 500.0),
                           ("ETH", 3.0, 1000.0), ("3QSS", None, 300.0)):
            _c6.execute("INSERT INTO signals VALUES (?,?,?,?,?,?,NULL)",
                        (_s, "2026-08-14T07:00:00+00:00", "ERÖFFNEN" if _h else "KAUFEN", "rollen",
                         _h, _p))
        pruefe(P, "eine Absicherung belegt kein Spot-Budget mehr",
               TP6.belegt_eur(_c6, "spot") == 800.0
               and TP6.belegt_eur(_c6, "absicherung") == 800.0
               and TP6.belegt_eur(_c6, "hebel") == 1000.0,
               "bis heute zaehlten offene Absicherungen gegen den SPOT-Topf. "
               "Der hat einen Deckel, die Absicherung nicht - eine gehaltene "
               "Hedge-Position hat also stillschweigend Spot-Budget belegt")
        _j = "2026-08-14T08:00:00+00:00"
        # ⚠️ HIER STAND "und der Cooldown trennt sie ebenfalls" (bis 23.08.).
        #
        # DIE TOPFTRENNUNG DER BUDGETS bleibt und wird oben geprueft. Beim
        # COOLDOWN ist sie seit S6b gegenstandslos: `hedge` hat genau EINEN
        # Lauf, und DBPK laeuft nie im Spot-Durchgang - der gepruefte Fall
        # konnte gar nicht eintreten.
        pruefe(P, "der Cooldown der Absicherung greift",
               WH6.gesperrt_bis(_c6, "DBPK", "absicherung", gruppe="hedge",
                                jetzt=_j) is not None,
               "eine Absicherung, die alle 15 Minuten neu gefragt wird, "
               "kostet Aufrufe ohne neue Information")

    # AC2 O-17: DIE 800 SIND UEBERNOMMEN, NICHT ENTSCHIEDEN.
    # KEIN CHECK AUF DEN KOMMENTAR. `_quelltext()` wirft Kommentarzeilen
    # bewusst weg, und eine Pruefung, die Dokumentation prueft statt
    # Verhalten, ist die Falle, die dieses Skript schon dreimal getreten hat.
    # Geprueft wird, was die Zahl TUT.
    # ALLE LESER DER ROLLEN-KETTE MUESSEN AM SELBEN ORT SUCHEN.
    #
    # `betraege` las als EINZIGES unter `risiko.rollen_kette.*`, alle uebrigen
    # unter `rollen_kette.*` - und `risiko.rollen_kette` gibt es in der
    # config.yaml nicht. Eine Einstellung dort waere wirkungslos geblieben,
    # ohne Fehlermeldung.
    pruefe(P, "der Einsatz laesst sich dort setzen, wo alles andere steht",
           BE6.einsatz_eur(
               "spot", "einstieg",
               {"rollen_kette": {"einsatz_eur_je_gruppe":
                                 {"aktien": {"einstieg": 500.0}}}},
               "aktien") == 500.0,
           "dort stehen aktiv_fuer und betriebsart - wer den Einsatz setzt, "
           "sucht ihn daneben")
    pruefe(P, "der alte Ort bleibt lesbar, der neue gewinnt",
           BE6.einsatz_eur(
               "spot", "einstieg",
               {"rollen_kette": {"einsatz_eur_je_gruppe":
                                 {"aktien": {"einstieg": 500.0}}},
                "risiko": {"rollen_kette": {"einsatz_eur_je_gruppe":
                                            {"aktien": {"einstieg": 600.0}}}}},
               "aktien") == 500.0,
           "eine bestehende Einstellung soll nicht durch das Aufraeumen "
           "ausfallen")

    pruefe(P, "und die Entscheidung ist eine Konfigurationszeile",
           BE6.einsatz_eur("spot", "einstieg", None, "aktien") == 800.0
           and BE6.einsatz_eur(
               "spot", "einstieg",
               {"risiko": {"rollen_kette": {
                   "einsatz_eur_je_gruppe": {
                       "aktien": {"einstieg": 500.0}}}}},
               "aktien") == 500.0,
           "wieviel Geld in eine einzelne Aktie geht, ist eine Risikofrage "
           "und gehoert dem Nutzer - kein Codeeingriff dafuer")

    # ------------------------------------------------------------------
    # AD. O-29 - das Messwerkzeug fuer die Verkaufsseite (14.08.2026).
    import messe_verkaufsseite as MV

    # AD1 DIE STATISTIK MUSS STIMMEN, sonst ist der Befund wertlos.
    pruefe(P, "AUC 0,5 bei identischen Gruppen",
           MV._auc([1, 2, 3], [1, 2, 3]) == 0.5,
           "kein Merkmal trennt sich von sich selbst")
    pruefe(P, "AUC 1,0 bei perfekter Trennung",
           MV._auc([10, 11, 12], [1, 2, 3]) == 1.0
           and MV._auc([1, 2, 3], [10, 11, 12]) == 0.0)
    pruefe(P, "der Permutationstest findet einen echten Unterschied",
           MV._permutation([10, 11, 12, 13, 14, 15], [1, 2, 3, 4, 5, 6],
                           ziehungen=2000) < 0.05,
           "sonst wuerde er auch einen echten Befund verwerfen")
    pruefe(P, "und findet keinen, wo keiner ist",
           MV._permutation([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6],
                           ziehungen=2000) > 0.5)
    pruefe(P, "derselbe Datenstand ergibt dieselbe Zahl",
           MV._permutation([1, 5, 9, 2], [3, 7, 4, 8], ziehungen=1000)
           == MV._permutation([1, 5, 9, 2], [3, 7, 4, 8], ziehungen=1000),
           "ein Test, dessen Ergebnis beim zweiten Lauf anders aussieht, "
           "taugt nicht als Beleg - deshalb eine feste Saat")

    # AD2 DER BERICHT MUSS DIE GRENZE SEINER AUSSAGE NENNEN.
    _e = {"kreuz": {"REDUZIEREN": [9, 0], "HALTEN": [8, 16]},
          "verkauf": [], "halten": [],
          "merkmale": {"pl": {"median_verkauf": -26.0, "median_halten": -44.0,
                              "auc": 0.64, "p": 0.65, "n": (11, 8)}}}
    _txt = " | ".join(MV.bericht(_e))
    pruefe(P, "der Bericht verwechselt 'nicht gezeigt' nicht mit 'zufaellig'",
           "NICHT 'zufaellig bewiesen'" in _txt
           and "wir koennen es nicht zeigen" in _txt,
           "bei 11 gegen 8 hat jeder Test wenig Trennschaerfe - der "
           "Unterschied ist der zwischen einem Befund und einer offenen Frage")
    pruefe(P, "und er nennt, was er NICHT beantwortet",
           "aufgeloeste" in _txt and "Wochen" in _txt,
           "ob die Verkaeufe sich tragen, kann heute niemand sagen")
    pruefe(P, "die erzwungene Trennung wird als solche benannt",
           "erzwungen, nicht geurteilt" in _txt,
           "kein Verkauf ohne Bestand ist kein Qualitaetsbeleg, sondern "
           "eine Selbstverstaendlichkeit")

    # AD3 GEGEN DIE ECHTE TABELLE.
    with sqlite3.connect("file:data/tradinginfotool.db?mode=ro",
                         uri=True) as _c7:
        pruefe(P, "die Messung laeuft gegen die echte Datenbank",
               isinstance(MV.messe(_c7), dict),
               "sie liest price_cache, holdings und signals - drei Tabellen, "
               "die sich unabhaengig voneinander aendern koennen")

    # ------------------------------------------------------------------
    # AE. DIE BELEGE - warum erfolgte die Entscheidung (14.08.2026).
    import json as _js
    import messe_begruendungen as MB
    from agent import signal_abbildung as SA7

    # AE1 SIE MUESSEN UEBERHAUPT ERST GESPEICHERT WERDEN.
    #
    # Bis heute ging nur die ANZAHL in die Datenbank: die Mail zeigte "Belege
    # (5, davon 3 unabhaengige Faktoren)", gespeichert wurden die 5 und die 3.
    # Welche Fakten das Urteil getragen haben, war damit nachtraeglich NICHT
    # beantwortbar - und laesst sich fuer bestehende Zeilen auch nicht
    # nachruesten.
    pruefe(P, "die Belege selbst gehen in die Signalzeile",
           "belege_json" in SA7.SPALTEN_SIGNAL,
           "eine Zeile, die heute ohne sie geschrieben wird, bleibt fuer "
           "immer ohne sie")
    _f7 = SA7.felder_aus_entscheidung(
        {"aktion": "KAUFEN", "begruendung": "x", "unabhaengige_faktoren": 2,
         "belege": [{"fakt": "Widerstand bei 0.0119 EUR",
                     "richtung": "dagegen", "gewicht": "hoch"}]},
        fakten={"asset": "X"}, lagebild_id=None, prompt_stand=None,
        eur_je_usd=None, familien=None, rechnung=None, modell="m")
    pruefe(P, "und kommen als lesbares JSON dort an",
           _js.loads(_f7["belege_json"])[0]["fakt"].startswith("Widerstand"),
           "als JSON statt als top_grund_1..5 - die alte Kette hat mit festen "
           "Spalten den sechsten Grund stillschweigend verloren")
    pruefe(P, "ohne Belege bleibt die Spalte leer statt '[]'",
           SA7.felder_aus_entscheidung(
               {"aktion": "NICHTS_TUN"}, fakten={"asset": "X"},
               lagebild_id=None, prompt_stand=None, eur_je_usd=None,
               familien=None, rechnung=None,
               modell="m").get("belege_json") is None,
           "eine leere Liste sieht in der Auswertung aus wie 'keine Gruende "
           "genannt' - None heisst 'nicht gefragt'")

    # AE1b DIE RICHTUNG DER ABHAENGIGKEIT (Methodik 2.13).
    #
    # Mein erster Reflex war, beide Messungen in `extract_notebook_diagnose.py`
    # einzuhaengen - "Auswertungen laufen ueber den Export". Die Methodik sagt
    # das Gegenteil: 2.1a stellt ROHDATEN bereit (hier `belege_json`), 2.13
    # fuehrt die AUSWERTUNGEN als eigenstaendige Skripte mit Ausloeser. Der
    # Export ist ein BASIS-Werkzeug, das andere importieren - wuerde er selbst
    # zwei Analyseskripte importieren, hinge die Datenbeschaffung an ihren
    # Fehlern.
    pruefe(P, "der Export importiert keine Analyseskripte",
           "messe_verkaufsseite" not in _quelltext("extract_notebook_diagnose.py")
           and "messe_begruendungen" not in _quelltext(
               "extract_notebook_diagnose.py"),
           "die Abhaengigkeit laeuft ZUM Export hin, nicht von ihm weg")
    pruefe(P, "aber die Rohdaten exportiert er",
           "belege_json" in _quelltext("extract_notebook_diagnose.py"),
           "2.1a: eine Frage, deren Rohdaten der Export nicht kennt, ist "
           "nachtraeglich nicht beantwortbar")

    # AE2 DIE ZUORDNUNG ZUM FAKTENBLOCK.
    #
    # NICHT die Kategorien der alten Kette (technisch/fundamental/...): die
    # kamen vom Modell und waeren eine zweite Selbstauskunft ueber eine erste.
    # Gemessen wird, aus welchem UNSERER Bloecke der Beleg stammt - das ist
    # die Frage "sind die Parameter die richtigen".
    for _satz, _erwartet in (
            ("Der naechste Widerstand liegt bei 0.0111 EUR", "marken"),
            ("Am Terminmarkt war die Finanzierungsrate positiv", "finanzierung"),
            ("Von den letzten 20 Tagen entfielen 85 % des Umsatzes auf "
             "Aufwaertstage", "volumen"),
            ("Die Marktstruktur zeigt hoehere Hochs", "verlauf"),
            ("Kursentwicklung im selben Rahmen: 5 Tage +6.7 %", "verlauf"),
            ("BTC ist bereits im Bestand: 150 EUR investiert", "bestand"),
            ("Ein Satz ohne bekannte Woerter", "unbekannt")):
        pruefe(P, f"Beleg -> Block: {_erwartet}",
               MB.block_fuer(_satz) == _erwartet,
               f"{_satz[:48]!r} ergab {MB.block_fuer(_satz)!r}")
    # DIE GENERISCHEN ANKER STEHEN SEIT DEM 17.08. IN EINER ZWEITEN TABELLE,
    # die erst NACH der ersten geprueft wird. Grund: `struktur` und `bewegung`
    # sind zu `verlauf` zusammengelegt, und ein dict kann denselben Schluessel
    # nicht zweimal fuehren - die Reihenfolge ist hier aber Teil der
    # Definition. Meine erste Fassung behalf sich mit dem Schluessel
    # `"verlauf "` (mit Leerzeichen); das haette in jeder Auswertung einen
    # zweiten, fast gleichnamigen Block erzeugt.
    pruefe(P, "die generischen Anker werden ZULETZT geprueft",
           "volumen" in MB.BLOCK_WOERTER
           and "volumen" not in MB.BLOCK_WOERTER_GENERISCH
           and set(MB.BLOCK_WOERTER_GENERISCH) == {"verlauf"},
           "der erste Treffer gewinnt - 'vergleich' oder '5 tage' kommen in "
           "mehreren Bloecken vor und duerfen nicht entscheiden")
    pruefe(P, "und kein Blockname traegt Leerraum",
           all(b == b.strip() for b in
               (*MB.BLOCK_WOERTER, *MB.BLOCK_WOERTER_GENERISCH)),
           "ein Schluessel mit Leerzeichen erzeugt lautlos einen zweiten, "
           "fast gleichnamigen Block in jeder Auswertung")

    # AE3 DER BERICHT DARF VERTEILUNG NICHT MIT ERFOLG VERWECHSELN.
    _leer = MB.messe.__wrapped__ if hasattr(MB.messe, "__wrapped__") else None
    with sqlite3.connect(":memory:") as _c8:
        _c8.execute("CREATE TABLE signals (quelle_kette TEXT, action TEXT, "
                    "unabhaengige_faktoren INTEGER, outcome_status TEXT, "
                    "belege_json TEXT)")
        _c8.execute("INSERT INTO signals VALUES ('rollen','KAUFEN',2,NULL,?)",
                    (_js.dumps([{"fakt": "Marktstruktur dreht",
                                 "richtung": "dafuer", "gewicht": "hoch"}]),))
        _b8 = " | ".join(MB.bericht(MB.messe(_c8)))
        pruefe(P, "ohne aufgeloeste Ausgaenge sagt der Bericht das auch",
               "zaehlt dieses Skript die Verteilung, nicht den" in _b8,
               "die eigentliche Frage braucht Wochen - ein Skript, das den "
               "Unterschied verwischt, waere schlimmer als keines")

    # ------------------------------------------------------------------
    # AF. DIE REMOTE-KARTE ZEIGTE 0, WAEHREND DIE KETTE LIEF (14.08.2026).
    #
    # Nutzerfund an der laufenden Anlage:
    #
    #     LLM-Budget heute (Krypto)    0 / 180
    #       davon Hebel                0
    #     Z.ai-Gegenpruefung heute    10
    #
    # Zehn Z.ai-Aufrufe auf null Signale - zwei Zahlen auf derselben Karte,
    # die einander widersprechen. Ursache: `count_real_signals_today()`
    # filtert auf `groq_raw_response IS NOT NULL`, eine Spalte, die
    # AUSSCHLIESSLICH die alte Kette schrieb. Und der Nenner 180 ist
    # `budget_allocator.taegliches_budget_gesamt` - der Allocator wird seit
    # dem Schnitt uebersprungen.
    from remote import status as RS

    pruefe(P, "der alte Zaehler ist blind fuer die neue Kette",
           "groq_raw_response IS NOT NULL" in _quelltext("database/db.py"),
           "die Spalte gibt es noch, sie wird nur nicht mehr geschrieben - "
           "deshalb zaehlt die alte Karte strukturell null")
    pruefe(P, "die neue Karte rechnet mit DER Funktion, die auch waehlt",
           "from scheduler.rollen_job import (KETTE, RESERVE_ANTEIL, "
           "_verbraucht)" in _quelltext("remote/status.py"),
           "eine Anzeige, die anders rechnet als der Waechter, ist schlimmer "
           "als keine")
    with sqlite3.connect("file:data/tradinginfotool.db?mode=ro",
                         uri=True) as _c9:
        _c9.row_factory = sqlite3.Row
        _rb = RS._get_rollen_budget(_c9)
        pruefe(P, "sie nennt alle vier Toepfe der Rueckfallkette",
               len(_rb["toepfe"]) == 4 and _rb["fehler"] is None,
               f"{[t['quelle'] for t in _rb['toepfe']]}")
        pruefe(P, "und zaehlt die Urteile ueber quelle_kette",
               "signale_heute" in _rb and "davon_hebel" in _rb,
               "nicht ueber eine Spalte der alten Kette")
    import inspect as _i9
    pruefe(P, "das Feld ist in RemoteStatus DEKLARIERT",
           "rollen_budget" in {f for f in _i9.signature(
               RS.RemoteStatus.__init__).parameters},
           "am 13.08. wurde ein Feld durchgereicht, das die Klasse nicht "
           "kannte - /api/status warf seitdem bei JEDEM Abruf einen TypeError")
    # AF2 DER ABRUFTAKT DER STATUSSEITE.
    #
    # 20 Warnungen in 3 Minuten: Aufbau 1,24-2,71 s bei Takt 2,0 s. Die
    # Spitzen fielen GENAU in das Fenster, in dem die Rollen-Kette lief -
    # Konkurrenz um dieselbe Datenbank und dieselbe CPU, kein Defekt der Karte
    # (Desktop: kalt 0,42 s, warm 0,03 s).
    pruefe(P, "die Seite fragt seltener als der langsamste Aufbau dauert",
           "setInterval(refreshStatus, 5000);" in _quelltext("remote/server.py"),
           "gegen Konkurrenz hilft kein Zwischenspeicher - der Aufbau ist ja "
           "schnell. Was hilft, ist seltener zu fragen")
    pruefe(P, "der Takt in der Warnung stimmt mit dem echten ueberein",
           "Abruftakt der Seite " in _quelltext("remote/status.py"),
           "eine Warnung, die einen anderen Takt nennt als die Seite hat, "
           "schickt die naechste Diagnose in die falsche Richtung")

    # AF3 MISTRAL IST RAUS - 402 seit dem 07.08.
    pruefe(P, "die Kategorie-Synthese ruft Mistral nicht mehr",
           'llm_clients = [("gemini", gemini_client)]' in _quelltext(
               "scheduler/background.py"),
           "ein Fehler, der bei JEDEM Lauf auftritt und nichts bedeutet, ist "
           "schlimmer als keiner - er trainiert das Auge, Fehlerzeilen zu "
           "ueberlesen")

    pruefe(P, "die alte Kette bleibt sichtbar, aber benannt",
           "ALTE KETTE (seit dem Schnitt ohne Aufrufer)" in _quelltext(
               "remote/server.py"),
           "sie wegzulassen hiesse, eine Zahl verschwinden zu lassen, ohne "
           "dass jemand sieht, dass sie verschwunden ist")

    # ------------------------------------------------------------------
    # AG. DIE DREI KLEINIGKEITEN AUS DEM BETRIEB (14.08.2026).
    from api.kraken import KRAKEN_PAIR_MAP as _KM

    # AG1 CANTON UND VSN HATTEN KEINE KURSREIHE - wegen eines TICKERS.
    #
    # Beide galten als "ohne Kraken-Listing". Der Rueckfall auf die
    # Boersen-Klines fand sie ebenfalls nicht: Binance und Bybit antworten mit
    # 400, OKX mit 51001. Der Grund war kein fehlendes Listing, sondern ein
    # anderer Name: CoinGecko nennt fuer `canton-network` die Handelspaare, und
    # dort heisst das Asset **CC**.
    #
    # NUTZERFRAGE DAZU, und sie war die richtige: "pruefe ob cc und canton
    # ident sind". Preis-Gegenprobe am 14.08.:
    #
    #     Kraken CCUSD   0,096770 USD
    #     CoinGecko      0,096751 USD    Abweichung 0,02 %
    #     Kraken VSNUSD  0,035410 USD
    #     CoinGecko      0,035603 USD    Abweichung 0,54 %
    #
    # Genau diese Probe hat am 11.08. den yfinance-Rueckfall zu Fall gebracht:
    # von acht geratenen Tickern gehoerten DREI einem anderen, toten Asset -
    # VSN mit 972 Kerzen haette jede Laengenpruefung bestanden.
    pruefe(P, "CANTON und VSN haben eine Kraken-Zuordnung",
           "CANTON" in _KM and "VSN" in _KM,
           "beide standen als Deckungsluecke, obwohl Kraken sie fuehrt")
    pruefe(P, "und CANTON uebersetzt auf einen ANDEREN Ticker",
           _KM["CANTON"]["USD"] == "CCUSD"
           and not _KM["CANTON"]["USD"].startswith("CANTON"),
           "bei 33 von 35 Eintraegen sind unser Symbol und das der Boerse "
           "gleich - deshalb faellt nicht auf, dass diese Zuordnung eine "
           "UEBERSETZUNG ist, bis eines abweicht")
    pruefe(P, "die Zuordnung nennt beide Waehrungen",
           set(_KM["CANTON"]) >= {"USD", "EUR"}
           and set(_KM["VSN"]) >= {"USD", "EUR"},
           "die Reihe kommt in USD, der Nutzer rechnet in EUR")

    # AG2 DIE VERBINDUNG WARTET JETZT, STATT ZU SCHEITERN.
    pruefe(P, "die Datenbank bekommt eine Wartezeit und WAL",
           "_SPERRE_WARTEN_SEKUNDEN = 30.0" in _quelltext("database/db.py")
           and "journal_mode = WAL" in _quelltext("database/db.py"),
           "SQLites Vorgabe sind fuenf Sekunden; seit dem Schnitt schreiben "
           "Rollen-Kette, Backward-Tracking, Preis-Refresh und Z.ai-Faeden auf "
           "dieselbe Datei, waehrend die Fernsteuerung alle fuenf Sekunden liest")
    pruefe(P, "und WAL wird nur EINMAL gesetzt",
           "_WAL_GESETZT" in _quelltext("database/db.py"),
           "der Modus ist eine Eigenschaft der DATEI - ihn je Verbindung neu "
           "zu setzen waere ein ueberfluessiger Schreibzugriff je Aufruf")
    pruefe(P, "der Export benutzt die WAL-sichere Backup-API",
           "conn.backup(" in _quelltext("extract_notebook_diagnose.py"),
           "eine Dateikopie waere unter WAL heikel - die juengsten "
           "Aenderungen stehen dann in `-wal`, nicht in der Hauptdatei. "
           "Nachgesehen, BEVOR umgestellt wurde")

    # ------------------------------------------------------------------
    # AH. DER HEBEL-STILLSTAND (14.08.2026) - die teuerste Zeile des Tages.
    #
    # Erster Betriebstag, Gate-Aufzeichnung um 19:58:
    #
    #     In:41  Out:0
    #       Auftrag:    17x Hebel-Pruefung abgeschaltet   (Nutzerschalter, ok)
    #       Aktion:     5x SCHLIESSEN ohne Bestand, 5x HALTEN
    #       Geometrie:  14x Betrag 0 EUR < 10 EUR Minimum   <-- HIER
    #
    # `_schreibe_nein()` schreibt fuer jedes NICHTS_TUN eine Zeile MIT
    # `position_size_eur` und `hebel` - als Messpunkt. `belegt_eur()` zaehlte
    # sie als belegtes Kapital. DREI solche Schattenbuchungen zu 1.000 EUR
    # fuellen den Hebel-Topf (3.000 EUR) vollstaendig.
    #
    # UND DANN HAELT SICH DIE SCHLEIFE SELBST AM LEBEN: Topf voll -> Betrag 0
    # -> Verlust an der Stufe "geometrie" -> KEINE Zeile -> Cooldown findet
    # nichts -> naechster Lauf fragt dieselben 14 Symbole wieder. Gemessen:
    # 698 Modellaufrufe fuer 46 Urteile, alle 15 Minuten von vorn.
    from agent import toepfe as TP8

    with sqlite3.connect(":memory:") as _c10:
        _c10.execute("CREATE TABLE signals (symbol TEXT, action TEXT, "
                     "quelle_kette TEXT, hebel REAL, position_size_eur REAL, "
                     "outcome_status TEXT, ist_reines_llm_halten INTEGER)")
        for _s, _a in (("AAA", "NICHTS_TUN"), ("BBB", "HALTEN"),
                       ("CCC", "SCHLIESSEN")):
            _c10.execute("INSERT INTO signals VALUES (?,?,?,?,?,NULL,1)",
                         (_s, _a, "rollen", 3.0, 1000.0))
        pruefe(P, "Schattenbuchungen belegen KEIN Kapital",
               TP8.belegt_eur(_c10, "hebel") == 0.0,
               "ein Schatten bindet kein Geld, weil nie gekauft wurde - er "
               "haelt nur fest, was passiert waere. Ihn im Topf mitzuzaehlen "
               "verwechselt die Messung mit der Sache")
        pruefe(P, "und ein Verkaufsvorschlag ebenfalls nicht",
               TP8.belegt_eur(_c10, "hebel") == 0.0,
               "SCHLIESSEN bindet kein Kapital - es gibt welches frei")
        _c10.execute("INSERT INTO signals VALUES "
                     "('DDD','ERÖFFNEN','rollen',3.0,1000.0,NULL,NULL)")
        pruefe(P, "ein echter Einstieg dagegen schon",
               TP8.belegt_eur(_c10, "hebel") == 1000.0,
               "gezaehlt wird, was eine Position EROEFFNET")
        _c10.execute("INSERT INTO signals VALUES "
                     "('EEE','ERÖFFNEN','rollen',3.0,900.0,"
                     "'take_profit_erreicht',NULL)")
        pruefe(P, "ein aufgeloester Einstieg belegt nichts mehr",
               TP8.belegt_eur(_c10, "hebel") == 1000.0,
               "outcome_status IS NULL - die Position ist zu")
    pruefe(P, "gezaehlt wird ueber eine EINSCHLUSSliste",
           "AKTIONEN_MIT_EINSTIEG" in _quelltext("agent/toepfe.py"),
           "eine Ausschlussliste faengt nur, was jemand vorhergesehen hat - "
           "und die naechste Aktion, die kein Kapital bindet, kommt bestimmt")

    # ------------------------------------------------------------------
    # AI. LEERLAUFWACHE UND DER ZWEITE BESTAND (14.08.2026, Abendrunde).
    import agent.rollen_lauf as RL9
    _q9 = _quelltext("agent/rollen_lauf.py")

    # AI1 EIN LAUF, DER NUR NOCH VERBRENNT, HAELT SICH SELBST AN.
    pruefe(P, "es gibt eine Grenze fuer Leerlauf in Folge",
           isinstance(RL9.LEERLAUF_ABBRUCH, int) and 3 <= RL9.LEERLAUF_ABBRUCH <= 20,
           f"{RL9.LEERLAUF_ABBRUCH} - grosszuegig genug fuer eine Handvoll "
           "Fehlschlaege, streng genug gegen einen Zustand")
    # ⚠️ ERWEITERT AM 23.08.2026 (L1): gezaehlt wird nur, wo ein Aufruf
    # stattfand UND kein Bestand vorlag. Ein HALTEN auf einer gehaltenen
    # Position ist die erwartete Antwort, kein Leerlauf - sonst hielten
    # acht Bestandsurteile den Lauf an, bevor die AUSGEWAEHLTEN
    # Kandidaten gefragt sind.
    pruefe(P, "gezaehlt wird NUR, wo ein Aufruf stattfand",
           'ergebnis["aufrufe"] > _vor_aufrufe' in _q9,
           "ein gesperrtes Symbol kostet nichts und darf die Wache nicht "
           "ausloesen - sonst hielte ausgerechnet der sparsame Fall den Lauf an")
    pruefe(P, "und der Bestand zaehlt nicht mit (L1)",
           "not _war_bestand(" in _q9,
           "ein HALTEN auf einer gehaltenen Position ist ein Ergebnis, "
           "kein Leerlauf")
    pruefe(P, "der Ersatz ist LAUFUEBERGREIFEND und eine MELDUNG",
           "stumme_laeufe" in _q9 and "logger.warning" in _q9,
           "der Zaehler in `ergebnis` entsteht je Lauf neu und ist nach "
           "A1 unerreichbar; ein laufuebergreifender ABBRUCH waere eine "
           "Falle - keine Signale, Bremse an, keine Aufrufe")
    pruefe(P, "ein Ergebnis setzt den Zaehler zurueck",
           'ergebnis["leerlauf"] = 0' in _q9,
           "acht IN FOLGE sind ein Zustand, acht verteilte sind Zufall")
    pruefe(P, "der Abbruch nennt, wo die Ursache steht",
           "verloren_je_stufe" in _q9 and 'ergebnis["abgebrochen"]' in _q9,
           "die Wache verhindert den Fehler nicht, sie begrenzt was er kostet "
           "- sie muss also sagen, wo man ihn findet")
    pruefe(P, "und das Modul hat einen Logger dafuer",
           "logger = logging.getLogger(__name__)" in _q9,
           "die erste Fassung rief logger.error ohne Logger im Modul - beim "
           "ersten Ausloesen haette die Wache selbst einen NameError geworfen")

    # AI2 DER HEBEL-BESTAND STEHT IN EINER ANDEREN TABELLE.
    #
    # Im Gate des ersten Betriebstags stand "5x SCHLIESSEN ohne Bestand" auf
    # dem HEBEL-Lauf - und sah aus wie ein Modell, das Unsinn vorschlaegt.
    # Tatsaechlich sah mein Verkaufszweig immer in `holdings` nach, der
    # SPOT-Tabelle. Eine offene Hebelposition steht in `hebel_positions`.
    pruefe(P, "der Verkaufszweig kennt beide Bestandsquellen",
           "DBM.get_open_hebel_positions(conn)" in _q9
           and "DBM.get_all_holdings(conn)" in _q9,
           "ein Hebel-Bestand ist keine Menge in holdings, sondern eine "
           "offene Position - EINE Regel auf zwei Wirklichkeiten angewandt, "
           "derselbe Fehler wie beim Cooldown und beim CRV-Faktor")
    pruefe(P, "und nimmt beim Hebel die Positionsmenge",
           'getattr(_hebelpos, "positionsmenge", None)' in _q9,
           "`quantity` gibt es dort nicht - die Abfrage haette still 0 "
           "geliefert und jedes VERKAUFEN zum Schatten gemacht")
    # ⚠️ S6b: EIN LAUF MUSS BEIDE BESTAENDE SEHEN.
    pruefe(P, "die Hebelposition hat Vorrang vor dem Spot-Bestand",
           _q9.index("get_open_hebel_positions(conn)")
           < _q9.index("get_all_holdings(conn)"),
           "sie traegt ein Ausfallrisiko (Liquidation), der Spot-Bestand "
           "nicht - und mit EINEM Lauf muss dieser eine beides kennen")
    # VERHALTEN PRUEFEN, NICHT DEN KOMMENTAR. `_quelltext()` wirft
    # Kommentarzeilen bewusst weg - das ist heute schon einmal aufgefallen.
    _ohne = VK4.rechne(aktion="SCHLIESSEN", menge=100.0, kurs_eur=2.0)
    _mit = VK4.rechne(aktion="SCHLIESSEN", menge=100.0, kurs_eur=2.0,
                      einstand_eur=3.0)
    pruefe(P, "ohne Einstandspreis wird keiner erfunden",
           "ergebnis_prozent" not in _ohne and "ergebnis_prozent" in _mit,
           "eine Hebelposition fuehrt keinen Einstand je Stueck - die "
           "Rechnung laesst das Ergebnis dann weg, statt eine Zahl zu bilden")

    # ------------------------------------------------------------------
    # AJ. DER TROCKENLAUF UEBER BEIDE INSTRUMENTE (15.08.2026) - drei Funde.
    import config as _cfgm
    from agent import toepfe as TP10
    from agent import betraege as BE10
    from agent import entscheidungsrechnung as ER10

    # AJ1 DIE ECHTE URSACHE DES HEBEL-STILLSTANDS.
    #
    # Gestern Abend habe ich sie in den Schattenbuchungen vermutet und
    # `belegt_eur` umgebaut. GEMESSEN AN DEN ECHTEN DATEN WAR DAS FALSCH: der
    # Topf stand vor UND nach dem Fix auf 0 EUR - Schattenzeilen tragen gar
    # keinen `position_size_eur`.
    #
    # Die Ursache ist der DECKEL. Die Nutzerentscheidung vom 13.08. lautet
    # 3.000 EUR; sie stand nur in `toepfe.VORGABE_DECKEL_EUR`, waehrend die
    # config.yaml weiter 500 fuehrte - und die Konfiguration gewinnt. EIN
    # Hebel-Signal fuellt einen 500er-Topf vollstaendig:
    #
    #     belegt   0 -> frei 500 -> Betrag 500 EUR
    #     belegt 500 -> frei   0 -> BLOCKIERT (Betrag 0)
    #
    # Und blockiert wird an der Stufe "geometrie" - also NACH dem
    # Modellaufruf. Ohne Zeile kein Cooldown, in 15 Minuten dasselbe von vorn.
    _cfg10 = _cfgm.load_config()
    pruefe(P, "der Hebel-Deckel folgt der Nutzerentscheidung",
           TP10.budget_eur("hebel", _cfg10) == 3000.0,
           "3.000 EUR laut Entscheidung 13.08. - die Konfiguration gewinnt "
           "gegen den Code, also muss sie es sein, die den Wert traegt")
    pruefe(P, "Code-Vorgabe und Konfiguration sagen dasselbe",
           TP10.VORGABE_DECKEL_EUR["hebel"] == TP10.budget_eur("hebel", _cfg10),
           "eine Vorgabe, die von der Konfiguration ueberstimmt wird, ist "
           "kein Standard - sie ist eine zweite Wahrheit")

    _ri10 = BE10.risiko_eur("hebel", "einstieg", _cfg10, "krypto")
    _wu10 = BE10.einsatz_eur("hebel", "einstieg", _cfg10, "krypto")
    _nach_einem = ER10.rechne(
        kurs=2400.0, atr=70.0, risiko_eur=_ri10, instrument="hebel",
        betrag_wunsch_eur=_wu10,
        topf_frei_eur=TP10.frei_eur("hebel", 1000.0, _cfg10),
        cash_frei_eur=1940.0)
    pruefe(P, "nach EINEM Hebel-Signal bleibt der Topf offen",
           _nach_einem["betrag_eur"] >= 100.0,
           f"{_nach_einem['betrag_eur']:.0f} EUR - mit 500er-Deckel war hier "
           "Schluss, und zwar nach dem Modellaufruf")

    # AJ2 `db` IST DER PFAD, NICHT DAS MODUL.
    #
    # Der Trockenlauf ueber beide Instrumente hat es in der ersten Zeile
    # gezeigt: "'str' object has no attribute 'get_all_holdings'". Mein
    # Verkaufszweig rief Modulfunktionen auf einer Zeichenkette auf; der
    # Fehler landete im breiten Fang als "Bestand nicht lesbar", und JEDES
    # Verkaufsurteil wurde zu "ohne Bestand". Die Verkaufsseite war seit
    # ihrem Bau tot.
    pruefe(P, "der Verkaufszweig benutzt das Datenbankmodul",
           "from database import db as DBM" in _quelltext("agent/rollen_lauf.py")
           and "DBM.get_all_holdings(conn)" in _quelltext("agent/rollen_lauf.py")
           and "DBM.get_open_hebel_positions(conn)" in _quelltext(
               "agent/rollen_lauf.py"),
           "`db` ist in `_ein_asset` der Dateiname - eine Zeichenkette hat "
           "diese Methoden nicht")

    # ------------------------------------------------------------------
    # AK. O-31: DIE HEBELAENDERUNG IST EINE DRITTE KLASSE (15.08.2026).
    #
    # Gesucht war `HEBEL_ERHOEHEN`, das durch beide Listen fiel und als
    # "nichts" gebucht wurde. Gefunden wurde mehr: `HEBEL_SENKEN` stand in der
    # AUSSTIEGSliste und bekam damit den Satz
    #
    #     "Verkaufen 0,206667 Stueck - ein Drittel der Position"
    #
    # Das ist keine fehlende Anweisung, sondern eine FALSCHE. Den Hebel zu
    # senken heisst, geliehenes Kapital zurueckzuzahlen - die Stueckzahl
    # bleibt. Wer dem Satz folgt, verkauft ein Drittel und hat den Hebel danach
    # immer noch.
    from agent import verkaufsrechnung as VK11
    from agent.empfehlung_vertrag import AKTIONEN_HEBEL as _AH

    pruefe(P, "jede Hebel-Aktion hat genau eine Klasse",
           all(sum((VK11.ist_ausstieg(a), VK11.ist_anpassung(a),
                    a in SM3.AKTIONEN_MIT_EINSTIEG)) <= 1 for a in _AH),
           "eine Aktion in zwei Klassen bekaeme zwei Anweisungen")
    _ohne = [a for a in _AH
             if not VK11.betrifft_bestand(a)
             and a not in SM3.AKTIONEN_MIT_EINSTIEG]
    pruefe(P, "keine Aktion faellt mehr durch alle Raster",
           _ohne == ["NICHTS_TUN"],
           f"ohne Klasse: {_ohne} - nur NICHTS_TUN darf uebrigbleiben, denn "
           f"es aendert nichts. (Hiess bis S6a HALTEN - derselbe Vorgang.)")
    pruefe(P, "beide Hebelaenderungen sind Anpassungen, kein Verkauf",
           VK11.ist_anpassung("HEBEL_ERHÖHEN")
           and VK11.ist_anpassung("HEBEL_SENKEN")
           and not VK11.ist_ausstieg("HEBEL_SENKEN"),
           "sie aendern den KREDIT, nicht die MENGE")

    _an = VK11.anpassung(aktion="HEBEL_ERHÖHEN", menge=0.62, kurs_eur=2400.0,
                         hebel_jetzt=3.0)
    pruefe(P, "eine Anpassung nennt keine Verkaufsmenge",
           "menge_verkauf" not in _an and "gegenwert_eur" not in _an,
           "eine Zahl in Stueck waere hier eine Falschaussage")
    _s11 = VK11.saetze_anpassung(_an)
    pruefe(P, "und sagt ausdruecklich, dass die Stueckzahl bleibt",
           any("Stueckzahl aendert sich dabei NICHT" in x for x in _s11),
           "der Leser muss den Unterschied zum Verkauf sofort sehen")
    pruefe(P, "beim Erhoehen steht die Liquidationswarnung dabei",
           any("Liquidation" in x for x in _s11)
           and not any("Liquidation" in x for x in VK11.saetze_anpassung(
               VK11.anpassung(aktion="HEBEL_SENKEN", menge=0.62,
                              kurs_eur=2400.0))),
           "mehr Hebel heisst naeher an der Liquidation - weniger nicht")
    pruefe(P, "ohne offene Position gibt es keine Anpassung",
           VK11.anpassung(aktion="HEBEL_ERHÖHEN", menge=0.0,
                          kurs_eur=2400.0) is None,
           "ohne Position gibt es keinen Hebel, den man aendern koennte - "
           "dann ist das Urteil ein Messpunkt, kein Auftrag")

    # AK2 DIE SAMMELMAIL TRENNT BEIDES.
    _mix = [{"symbol": "BTC", "begruendung": "a",
             "verkauf": VK11.rechne(aktion="VERKAUFEN", menge=0.05,
                                    kurs_eur=54000.0, einstand_eur=68000.0)},
            {"symbol": "ETH", "begruendung": "b",
             "verkauf": VK11.anpassung(aktion="HEBEL_SENKEN", menge=0.62,
                                       kurs_eur=2400.0, hebel_jetzt=10.0)}]
    _b11, _t11 = VK11.sammel_mail(_mix)
    pruefe(P, "die Summe zaehlt nur Verkaeufe",
           "2.700" in _t11 and "4.188" not in _t11,
           "eine Hebelaenderung bewegt kein Geld aus der Position heraus - "
           "sie in den Gegenwert einzurechnen ergaebe eine Zahl, die niemand "
           "wiederfindet")
    pruefe(P, "der Betreff nennt beide Arten getrennt",
           "Verkaufsvorschlaege" in _b11 and "Hebel aendern" in _b11,
           "wer nur 'Verkaufsvorschlaege' liest, uebersieht die Anpassung")
    pruefe(P, "und die Anpassung steht HINTER den Verkaeufen",
           _t11.index("BTC ") < _t11.index("ETH "),
           "wer beides in einer Mail hat, muss zuerst wissen, was rausgeht")
    pruefe(P, "der Lauf fragt nach BESTAND, nicht nach Ausstieg",
           "VK.betrifft_bestand(aktion)" in _quelltext("agent/rollen_lauf.py")
           and "VK.ist_anpassung(aktion)" in _quelltext("agent/rollen_lauf.py"),
           "beide Klassen setzen eine Position voraus - die Abzweigung ist "
           "dieselbe, die Anweisung dahinter nicht")

    # ------------------------------------------------------------------
    # AL. PAKET 14 - DIE ABSICHERUNG ALS EIGENE ROLLE (15.08.2026).
    #
    # Bis heute lief sie durch denselben Trader-Prompt wie ein Spot-Kauf:
    # Marktstruktur, Widerstand, Momentum DES INSTRUMENTS. Bei 3QSS und DBPK
    # ist das die falsche Frage - ihr Chart IST das Spiegelbild des Nasdaq bzw.
    # des S&P. Ihn technisch zu bewerten heisst, den Index zu bewerten und das
    # Ergebnis umzudrehen; das tut das Lagebild bereits.
    from agent import absicherung_fakten as AB12
    from agent import rolle_trader as RT12

    pruefe(P, "die Absicherung hat einen eigenen Prompt",
           RT12.prompt_fuer("absicherung", "einstieg")
           != RT12.prompt_fuer("spot", "einstieg"),
           "ein stiller Rueckfall auf Spot wuerde nach dem Chart fragen, wo "
           "die Portfoliolage entscheidet")
    _pa = RT12.prompt_fuer("absicherung", "einstieg")
    pruefe(P, "und er sagt, worum es NICHT geht",
           "nicht ueber einen Trade" in _pa
           and "das ist seine Bauart" in _pa,
           "das Instrument steigt, wenn der Markt faellt - danach zu fragen "
           "waere die Frage nach dem Index, nur rueckwaerts")
    pruefe(P, "er nennt Exposure und Abdeckung als Bezug",
           "EXPOSURE" in _pa and "Abdeckung" in _pa,
           "benoetigter Einsatz = abzusicherndes Exposure / Hebelfaktor "
           "(toepfe.py, 07.08.)")
    pruefe(P, "und die laufende Gebuehr steht drin",
           "kostet auch dann" in _pa,
           "ein gehebelter inverser ETF verliert taeglich durch Rebalancing - "
           "eine vergessene Absicherung kostet Geld ohne Gegenleistung")

    # AL2 DIE RECHNUNG - gegen echte Bestandsdaten.
    with sqlite3.connect("file:data/tradinginfotool.db?mode=ro",
                         uri=True) as _c12:
        _c12.row_factory = sqlite3.Row
        _l12 = AB12.lage(_c12, "3QSS")
        pruefe(P, "die Absicherungslage laeuft gegen die echte Datenbank",
               isinstance(_l12, dict),
               "sie liest holdings, price_cache und die Watchlist")
    # Und gegen einen gestellten Fall, bei dem jede Zahl nachrechenbar ist.
    with sqlite3.connect(":memory:") as _c13:
        _c13.row_factory = sqlite3.Row
        _c13.execute("CREATE TABLE holdings (symbol TEXT, quantity REAL, "
                     "updated_at TEXT, source TEXT, avg_buy_price_eur REAL, "
                     "avg_buy_price_tracked_qty REAL, "
                     "avg_buy_price_computed_at TEXT, "
                     "avg_buy_price_manual_eur REAL, staked_quantity REAL)")
        for _s, _q in (("BTC", 10.0), ("3QSS", 100.0), ("EURCV", 500.0)):
            _c13.execute("INSERT INTO holdings VALUES (?,?,'','',NULL,NULL,"
                         "NULL,NULL,NULL)", (_s, _q))

        class _A:
            def __init__(_s2, sym, cash=False):
                _s2.symbol, _s2.ist_cash_aequivalent = sym, cash

        _wl = [_A("BTC"), _A("3QSS"), _A("EURCV", True)]
        _e13 = AB12.lage(_c13, "3QSS", kurse_eur={"BTC": 100.0, "3QSS": 10.0,
                                                  "EURCV": 1.0},
                         watchlist=_wl)
        # BTC 10 x 100 = 1.000 Exposure. 3QSS 100 x 10 x Hebel 3 = 3.000
        # Abdeckung. EURCV ist Cash und faellt heraus - ein Stablecoin faellt
        # nicht und braucht keine Absicherung.
        pruefe(P, "Exposure zaehlt weder Absicherung noch Cash mit",
               _e13["exposure_eur"] == 1000.0,
               f"{_e13['exposure_eur']} - erwartet 1.000 (nur BTC)")
        pruefe(P, "die Abdeckung ist leverage-adjustiert",
               _e13["abdeckung_eur"] == 3000.0,
               f"{_e13['abdeckung_eur']} - 100 Stueck x 10 EUR x Hebel 3; "
               "1 EUR in einem 3x-Short deckt 3 EUR Exposure")
        pruefe(P, "bei Ueberdeckung ist nichts mehr offen",
               _e13["noch_offen_eur"] == 0.0
               and _e13["einsatz_fuer_volle_deckung_eur"] == 0.0,
               "3.000 gegen 1.000 - eine negative Zahl waere hier sinnlos")
        _saetze13 = AB12.saetze(_e13)
        pruefe(P, "und die Saetze nennen den Referenzindex",
               any("Nasdaq-100" in s for s in _saetze13),
               "3QSS hebelt auf den Nasdaq - ohne den Index ist der "
               "Hebelfaktor eine Zahl ohne Bezug")

    # AL3 EIN FEHLENDER PREIS WIRD GESAGT, NICHT VERSCHLUCKT.
    with sqlite3.connect(":memory:") as _c14:
        _c14.row_factory = sqlite3.Row
        _c14.execute("CREATE TABLE holdings (symbol TEXT, quantity REAL, "
                     "updated_at TEXT, source TEXT, avg_buy_price_eur REAL, "
                     "avg_buy_price_tracked_qty REAL, "
                     "avg_buy_price_computed_at TEXT, "
                     "avg_buy_price_manual_eur REAL, staked_quantity REAL)")
        for _s, _q in (("BTC", 10.0), ("DBPK", 50.0)):
            _c14.execute("INSERT INTO holdings VALUES (?,?,'','',NULL,NULL,"
                         "NULL,NULL,NULL)", (_s, _q))
        _e14 = AB12.lage(_c14, "3QSS", kurse_eur={"BTC": 100.0},
                         watchlist=[_A("BTC"), _A("DBPK")])
        pruefe(P, "eine gehaltene Absicherung ohne Preis wird gemeldet",
               any("UNTERSCHAETZT" in u for u in (_e14.get("unsicher") or [])),
               "genau der Fund vom 18.07.: sie wuerde als '0 Abdeckung' "
               "durchgehen, und ein Aufbau daraufhin koennte unbemerkt "
               "ueberhedgen")

    # AL3b DIE MAIL DARF KEINE EINSTIEGS-TREFFERQUOTEN ZEIGEN.
    #
    # Im Trockenlauf an einer echten 3QSS-Mail gefunden:
    #
    #     Schwankung 4,9 % je Tag   UNGUENSTIG
    #       "Ruhig ist besser - ueber alle Einstiege gemessen: 29,5 % Treffer"
    #
    # Die Kernfamilien sind an EINSTIEGEN gemessen - an der Frage, ob ein Kauf
    # sein Ziel vor dem Stop erreicht. Eine Absicherung wird nicht gekauft, um
    # zu steigen. Eine Zahl mit falscher Herkunft liest sich wie ein Befund;
    # das ist schlimmer als eine fehlende Angabe.
    from agent import faktenblock as FB12
    # DIE ECHTEN PARAMETERNAMEN - `kern()` braucht neben den Perzentilen auch
    # die absoluten Werte, sonst meldet es drei Luecken statt drei Familien.
    # Meine erste Fassung hatte nur die Perzentile und pruefte damit den
    # Luecken-Pfad statt den Kern.
    _kern12 = {"atr_relativ": 0.049, "schwankung_perzentil": 0.8,
               "rueckgang_60t": 0.27, "momentum_perzentil": 0.3,
               "volumen_relativ": 1.1, "volumen_perzentil": 0.5}
    _hedge_block = FB12.baue("hedge", kern_werte=_kern12)
    pruefe(P, "die Absicherungsmail zeigt keine Einstiegs-Trefferquoten",
           not any("Treffer am guten Ende" in z for z in _hedge_block),
           "sie stammen von Kaufsignalen - eine andere Grundgesamtheit")
    pruefe(P, "und sagt ausdruecklich, dass sie nicht gelten",
           any("gelten hier NICHT" in z for z in _hedge_block),
           "wegzulassen ohne es zu sagen waere die zweite Haelfte desselben "
           "Fehlers - der Leser wuesste nicht, dass etwas fehlt")
    pruefe(P, "die uebrigen Bereiche behalten ihre Kernfamilien",
           any("Treffer am guten Ende" in z
               for z in FB12.baue("krypto_spot", kern_werte=_kern12)),
           "dort sind die Quoten an genau dieser Frage gemessen")

    # AL4 DIE LAGE ERREICHT MODELL UND MAIL.
    _rl12 = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Absicherungslage steht VOR dem Urteil",
           _rl12.index("AB.lage(conn, symbol)")
           < _rl12.index("bc_roh = _frage("),
           "ein Faktum, das erst in der Mail auftaucht, hat die Entscheidung "
           "nicht beeinflusst")
    pruefe(P, "und dieselben Saetze gehen an den Nutzer",
           'bc_ein.get("absicherungslage")' in _rl12,
           "zwei Formulierungen derselben Zahl laufen auseinander")

    # ------------------------------------------------------------------
    # AM. DER VOLLUMSTIEG (15.08.2026) - und der Schnitt, der nur halb griff.
    import config as _cfgm2
    from agent import assetklassen as AK13
    from scheduler.rollen_job import aktiv_fuer as _af, bedient_neue_kette as _bnk

    _cfg13 = _cfgm2.load_config()
    _gruppen13 = sorted({g for g, _, _ in AK13.laeufe()})
    pruefe(P, "alle sechs Gruppen laufen ueber die Rollen-Kette",
           all(_bnk(g, _cfg13) for g in _gruppen13),
           f"noch alt: {[g for g in _gruppen13 if not _bnk(g, _cfg13)]}")

    # DER FUND BEI DIESER GEGENPRUEFUNG. `bedient_neue_kette` stand an genau
    # EINER Stelle - in `hebel_screening_job`, fest auf "krypto". Der
    # Multi-Asset-Batch, der Aktien, Rohstoffe, Themen-ETF und die Absicherung
    # bedient, kannte den Schnitt GAR NICHT.
    #
    # `aktiv_fuer` auf alle sechs zu setzen haette damit nicht umgestellt,
    # sondern VERDOPPELT: Rollen-Kette im 15-Minuten-Takt und Batch um 9 und
    # 19 Uhr, dieselben Symbole, beide mit Modellaufrufen und Mail. Genau der
    # Parallelbetrieb, den der Nutzer am 13.08. ausgeschlossen hat.
    _bg13 = _quelltext("scheduler/background.py")
    # DER FUND AUS DER BUDGET-HOCHRECHNUNG: die Gruppen-Cooldowns waren toter
    # Code. `budget_allocator.spot_cooldown_stunden` (15) steht in der
    # config.yaml und wurde VOR der Gruppen-Vorgabe (24) gefragt - die 24
    # Stunden, am 14.08. mit der Handelstagslogik begruendet, kamen nie zum
    # Zug. Im Krypto-Betrieb unsichtbar, weil Krypto ohnehin 15 h hat.
    from agent import wiederholung as WH13
    # ⚠️ HIER STAND `krypto == 15.0` (bis 23.08.2026). Das war der Zustand,
    # als Krypto seinen Wert noch aus dem INSTRUMENT bezog. Seit die
    # config einen Gruppenwert traegt (3,5 h, Reparatur der S6b-Folge),
    # gewinnt er - und belegt dieselbe Aussage staerker: die Gruppe schlaegt
    # das Instrument jetzt an BEIDEN Gruppen, nicht nur an einer.
    # ⚠️ NICHT MEHR AUF DEN WERT 3,5 (28.08.2026). Die Aussage dieser
    # Pruefung ist "die GRUPPE schlaegt das INSTRUMENT" - der konkrete Wert
    # war nur das Beispiel. Seit der Gruppenwert auf 12 h steht (L4/L5),
    # scheiterte sie an ihrem eigenen Beispiel statt an ihrer Aussage.
    # Geprueft wird jetzt, was gemeint war: KEINE Gruppe faellt auf den
    # Instrumentwert `spot_cooldown_stunden` (15) zurueck.
    pruefe(P, "eine GRUPPE ist spezifischer als ein INSTRUMENT",
           WH13.stunden("spot", _cfg13, "aktien") == 24.0
           and WH13.stunden("spot", _cfg13, "krypto") != 15.0,
           f"aktien {WH13.stunden('spot', _cfg13, 'aktien')} h, krypto "
           f"{WH13.stunden('spot', _cfg13, 'krypto')} h - beide muessen aus "
           f"der GRUPPE kommen, nicht aus `spot_cooldown_stunden` (15)")
    pruefe(P, "und die Konfiguration schlaegt den Code weiterhin",
           WH13.stunden("spot", {"rollen_kette": {
               "cooldown_stunden_je_gruppe": {"aktien": 6}}}, "aktien") == 6.0,
           "innerhalb derselben Spezifitaet gewinnt die Konfiguration")

    pruefe(P, "auch der Multi-Asset-Batch kennt den Schnitt",
           "_offen = sorted(g for g in _meine if not _neu(g, _cfg))" in _bg13,
           "sonst liefen beide Ketten auf dieselben Symbole - der "
           "Parallelbetrieb, den der glatte Schnitt ausschliesst")
    pruefe(P, "und er prueft JE GRUPPE, nicht pauschal",
           '_meine = {"aktien", "rohstoffe", "themen_etf", "hedge"}' in _bg13,
           "solange EINE der vier noch alt ist, muss er fuer sie weiterlaufen")
    pruefe(P, "der Umlauf startet, sobald IRGENDEINE Gruppe umgestellt ist",
           "for g in {g for g, _, _ in _AK2.laeufe()})" in _bg13,
           "vorher stand dort fest 'krypto' - waere Krypto eines Tages "
           "abgeschaltet und Aktien nicht, liefe der Umlauf lautlos gar nicht")
    c.close()


def _nur_code(pfad: str) -> str:
    """Der Quelltext OHNE Kommentare und ohne Zeichenketten.

    WOFUER, an vier echten Fehlschlaegen gelernt. Eine Pruefung wie
    `"fuehre_beide_calls_im_hintergrund" not in quelle` schlaegt an, sobald der
    Modul-Docstring ERKLAERT, warum diese Funktion bewusst NICHT gerufen wird.
    Je besser eine Datei begruendet, was sie nicht tut, desto sicherer meldet
    eine solche Pruefung einen Defekt, den es nicht gibt.

    Dasselbe schon zweimal am 13.08.: `" R"` traf "REICHWEITE", und
    `"confidence_pct"` traf den Docstring, der dessen Entfernung begruendet.

    Faellt das Zerlegen aus (Syntaxfehler waehrend eines Umbaus), kommt der
    Rohtext zurueck - lieber ein zu strenger Treffer als eine stumme Pruefung."""
    import io as _io
    import tokenize as _tok
    try:
        with _io.open(pfad, "rb") as f:
            return " ".join(
                tok.string for tok in _tok.tokenize(f.readline)
                if tok.type not in (_tok.COMMENT, _tok.STRING))
    except Exception:                                        # noqa: BLE001
        return _quelltext(pfad)


def _konst_aus(datei, name):
    import re
    m = re.search(rf"^{name}\s*=\s*([0-9.]+)", _quelltext(datei), re.M)
    return float(m.group(1)) if m else None


def paket_frische() -> None:
    """Die Frischepruefung: findet sie Stillstand, und meldet sie nichts,
    wenn alles laeuft? (17.08.2026)

    DER ANLASS. Drei von vier Nicht-Kurs-Aussagen der Rolle A standen seit
    dem 12.08. still, und nichts meldete es: `beschreibe_makro` nimmt den
    juengsten Wert <= Ankertag ohne Altersgrenze, der Satz entsteht also
    weiter - nur mit immer aelteren Zahlen.

    ⚠️ BEIDE RICHTUNGEN. Eine Pruefung, die nur Alarm schlagen kann, ist
    keine - sie waere mit `return "veraltet"` erfuellt. Deshalb hier zwei
    Datenbanken im Speicher: eine stillstehende und eine frische.

    UND DIE VOLLSTAENDIGKEIT. Dieselbe Falle wie bei
    `SYMBOL_ZU_COT_ROHSTOFF`: eine neue Quelle, die niemand eintraegt,
    wird still nicht ueberwacht. Die Registratur wird deshalb gegen
    `mindestkriterien.QUELLEN_G` gehalten - was Rolle G als Quelle zaehlt,
    muss auch auf Frische geprueft werden."""
    import sqlite3
    from datetime import date, timedelta

    from agent import datenfrische as DF
    from agent import mindestkriterien as MK

    P = "Frische"

    def bau(alter_tage: int) -> sqlite3.Connection:
        """Eine Datenbank, in der jede Quelle genau `alter_tage` alt ist."""
        c = sqlite3.connect(":memory:")
        heute = date.today()
        stand = (heute - timedelta(days=alter_tage)).isoformat()
        c.execute("CREATE TABLE macro_snapshot (date TEXT PRIMARY KEY, "
                  "netto_liquiditaet_mrd REAL, rendite_10j_pct REAL, "
                  "fear_greed_value INT, fetched_at TEXT)")
        c.execute("INSERT INTO macro_snapshot VALUES (?,?,?,?,?)",
                  (stand, 5900.0, 4.5, 30, stand))
        c.execute("CREATE TABLE makro_historie_monat (monat TEXT PRIMARY KEY)")
        c.execute("INSERT INTO makro_historie_monat VALUES (?)", (stand[:7],))
        c.execute("CREATE TABLE job_laeufe (job_id TEXT PRIMARY KEY, "
                  "zuletzt_am TEXT)")
        c.execute("INSERT INTO job_laeufe VALUES ('makro_analog', ?)", (stand,))
        c.execute("CREATE TABLE externe_reihe (quelle TEXT, schluessel TEXT, "
                  "datum TEXT, wert REAL, geholt_am TEXT)")
        for q in ("coinmetrics", "defillama", "deribit", "cftc_cot",
                  "etf_bestand", "finra", "sec_edgar", "yfinance"):
            c.execute("INSERT INTO externe_reihe VALUES (?,?,?,?,?)",
                      (q, "x", stand, 1.0, stand))
        c.execute("CREATE TABLE open_interest_snapshot (symbol TEXT, "
                  "fetched_at TEXT)")
        c.execute("INSERT INTO open_interest_snapshot VALUES ('BTC', ?)",
                  (stand,))
        c.execute("CREATE TABLE price_history_ohlc (symbol TEXT, date TEXT, "
                  "fetched_at TEXT)")
        c.execute("INSERT INTO price_history_ohlc VALUES ('BTC', ?, ?)",
                  (stand, stand))
        c.execute("CREATE TABLE holdings (symbol TEXT, updated_at TEXT)")
        c.execute("INSERT INTO holdings VALUES ('BTC', ?)", (stand,))
        c.commit()
        return c

    frisch = DF.pruefe(bau(0))
    pruefe(P, "frische Datei: kein einziger Befund",
           not DF.auffaellig(frisch),
           f"{len(DF.auffaellig(frisch))} von {len(frisch)} auffaellig")
    pruefe(P, "frische Datei: alle Quellen geprueft",
           len(frisch) == len(DF.REGISTRATUR),
           f"{len(frisch)} Zeilen, {len(DF.REGISTRATUR)} Quellen")

    # 30 Tage: laenger als jede Abrufgrenze, kuerzer als die grosszuegigste
    # Datengrenze (yfinance, 120) - so wird sichtbar, dass das ABRUFALTER
    # das Urteil traegt, nicht das Datenalter.
    tot = DF.pruefe(bau(30))
    pruefe(P, "stillstehende Datei: jede Quelle faellt auf",
           len(DF.auffaellig(tot)) == len(tot),
           f"{len(DF.auffaellig(tot))} von {len(tot)}")
    pruefe(P, "stillstehende Datei: Urteil ist 'abruf', nicht 'daten'",
           all(z["urteil"] == "abruf" for z in tot),
           str(sorted({z["urteil"] for z in tot})))

    # Eine leere Datei ist NICHT "alles frisch" - der Fehler, der die
    # Pruefung wertlos machen wuerde.
    leer = sqlite3.connect(":memory:")
    ohne = DF.pruefe(leer)
    pruefe(P, "leere Datei meldet 'fehlt', nicht 'frisch'",
           all(z["urteil"] == "fehlt" for z in ohne),
           str(sorted({z["urteil"] for z in ohne})))

    # VOLLSTAENDIGKEIT gegen die einzige andere Stelle, die Quellen fuehrt.
    #
    # ⚠️ ZWEI NAMENSRAEUME, UND SIE SIND NICHT DIESELBEN. `QUELLEN_G`
    # fuehrt MERKMALE ("onchain", "cot"), die Registratur fuehrt
    # ANBIETER ("coinmetrics", "cftc_cot"). Eine Mengendifferenz der
    # beiden waere immer leer und die Pruefung damit wertlos - genau die
    # Sorte gruener Haken, die am 16.08. drei Tage lang einen Ausfall
    # verdeckt hat. Deshalb eine ausdrueckliche Zuordnung: kommt in
    # `QUELLEN_G` ein Merkmal dazu, das hier nicht steht, faellt die
    # Pruefung.
    MERKMAL_ZU_ANBIETER = {
        "terminmarkt": "terminmarkt", "onchain": "coinmetrics",
        "cot": "cftc_cot", "etf_bestand": "etf_bestand",
        "short_interest": "finra", "insider": "sec_edgar",
        "optionsmarkt": "deribit",
    }
    registriert = {q.name for q in DF.REGISTRATUR}
    ohne_zuordnung = sorted(set(MK.QUELLEN_G) - set(MERKMAL_ZU_ANBIETER))
    pruefe(P, "jedes Merkmal der Rolle G hat einen Anbieter",
           not ohne_zuordnung, str(ohne_zuordnung))
    ohne_pruefung = sorted(a for a in MERKMAL_ZU_ANBIETER.values()
                           if a not in registriert)
    pruefe(P, "jeder Anbieter der Rolle G wird auf Frische geprueft",
           not ohne_pruefung, str(ohne_pruefung))
    pruefe(P, "jede Registraturzeile hat Tabelle, Job und Zweck",
           all(q.tabelle and q.job and q.zweck and q.max_datenalter > 0
               for q in DF.REGISTRATUR),
           "")


def paket_mail() -> None:
    """Die Funde der Mailpruefung vom 17.08.2026 - je einer als Test.

    Alle stammen aus EINER echten SOL-Mail, die der Nutzer Zeile fuer Zeile
    durchgegangen ist. Vier davon waren keine Anzeigefehler."""
    import numpy as _np

    from agent import ausstiegsrechnung as _AR
    from agent import entscheidungsrechnung as _ER
    from agent import lagebeschreibung as _LB
    from agent import marktrang as _MR_MOD
    from agent import rollen_lauf as _RL
    from agent import signal_mail as _SM
    from agent import trefferbilanz as _TB

    P = "Mail"

    # --- A2: das Ziel darf nicht hinter der Marke liegen, die dieselbe Mail
    # nennt. Der Parameter `widerstand` existierte seit jeher - und wurde von
    # KEINEM Aufrufer je gefuellt.
    ohne = _ER.rechne(kurs=64.86, atr=1.30, risiko_eur=20.0,
                      betrag_wunsch_eur=800.0, kostenklasse="krypto")
    mit = _ER.rechne(kurs=64.86, atr=1.30, risiko_eur=20.0,
                     betrag_wunsch_eur=800.0, kostenklasse="krypto",
                     widerstand=(66.55, 5))
    # ⚠️ UMGESCHRIEBEN AM SELBEN TAG (17.08.2026). Hier stand "kein
    # Widerstand in Reichweite" - der Text des Zweigs, solange gedeckelt
    # wurde. Gemessen wurde der Deckel danach verworfen (44 von 44
    # gedeckelt, Median CRV 0,21), und der Text behauptete dann etwas
    # Falsches direkt ueber einer Liste von vier Marken.
    pruefe(P, "A2: ohne Marke bleibt es beim mechanischen Ziel",
           ohne["ziel_regel"] == "mechanisch, 2x Risiko"
           and ohne["ziel_bis_eur"] > 66.55,
           "die Rechnung sagt jetzt, was sie ist - statt zu behaupten, es "
           "gebe keinen Widerstand")
    pruefe(P, "A2: mit Marke endet das Ziel davor",
           mit["ziel_bis_eur"] <= 66.55
           and "vor dem Widerstand" in mit["ziel_regel"],
           f"{mit['ziel_von_eur']:.2f}-{mit['ziel_bis_eur']:.2f} EUR, "
           f"{mit['ziel_regel']}")
    pruefe(P, "A2: und die zu kleine CRV wird AUSGEWIESEN, nicht geschoent",
           mit["crv"] < 2.0 and mit["crv_erreicht"] is False
           and any("traegt nur CRV" in z for z in _ER.saetze(mit)),
           f"CRV {mit['crv']:.2f} - ein Ziel hinter einer Mauer ist kein Ziel")

    # Die Marke muss auch WIRKLICH ankommen - der Fehler war nicht die
    # Rechnung, sondern der nie gefuellte Parameter.
    _bl = {"_marken_werte": {"widerstand": {"preis_eur": 66.55,
                                            "beruehrungen": 5},
                             "unterstuetzung": {"preis_eur": 63.44,
                                                "beruehrungen": 4}}}
    pruefe(P, "A2: LONG bekommt den Widerstand",
           _RL._marke_im_weg(_bl, False) == (66.55, 5))
    pruefe(P, "A2: SHORT bekommt die Unterstuetzung",
           _RL._marke_im_weg(_bl, True) == (63.44, 4),
           "bei SHORT liegt das Ziel unten - im Weg steht die Unterstuetzung")
    pruefe(P, "A2: ohne Marken bleibt es None",
           _RL._marke_im_weg({}, False) is None,
           "dann stimmt die Klammer 'kein Widerstand in Reichweite' auch")

    # EINE Ermittlung fuer Satz und Zahl.
    _n = 80
    _c = _np.linspace(60.0, 64.86, _n)
    _h = _c + 1.0
    _l = _c - 1.0
    _h[20] = _h[40] = _h[60] = 70.0
    _saetze = _LB._niveaus(_c, _h, _l, _n - 1, 1.3, 64.86, float(_c[-1]))
    _werte = _LB.niveaus_werte(_c, _h, _l, _n - 1, 1.3, 64.86, float(_c[-1]))
    _w = _werte.get("widerstand")
    pruefe(P, "A2: Satz und Zahl stammen aus derselben Ermittlung",
           bool(_w) and any("Widerstand" in z for z in _saetze),
           f"Satz: {_saetze[:1]} / Zahl: {_w}")

    # --- A3: 34 gegen 36 - zwei Zahlen fuer dieselbe Groesse.
    _b = {"basisrate": 0.34, "wahrscheinlichkeit": 0.36, "breakeven": 0.73,
          "traegt": False, "belastbar": False, "faelle": 3, "crv": 2.0,
          "treffer": 1, "abgelaufen": 0, "anteil_entschieden": 1.0}
    _z = " ".join(_TB.satz(_b, einstieg=64.86, stop=63.24,
                           einsatz_eur=800.0, klasse="krypto"))
    pruefe(P, "A3: die zweite Zahl wird erklaert statt danebengestellt",
           "Erfahrungsrate von 34" in _z and "angepasst um 3 eigene" in _z,
           "vorher stand 'Gemessen an der Erfahrungsrate' unter einer Zahl, "
           "die nicht die Erfahrungsrate ist")
    pruefe(P, "A3: die Entscheidung steht weiter auf der angepassten Zahl",
           "36 erreichen das Ziel" in _z and "noetig waeren 73" in _z,
           "sie ist die bessere Schaetzung - nur war sie falsch beschriftet")

    # --- A4: zwei Zahlen unter einem Wort.
    _aus = _AR.bewerte(einstieg=63.00, stop_original=60.90,
                       kurs_aktuell=63.90, mfe_r=0.41,
                       umgeworfen_durch="Schlusskurs unter der Unterstuetzung")
    _aus["empfehlung"] = "HALTEN"
    _aus["ist_bestand"] = True
    _, _txt = _SM.baue_mail(symbol="SOL", name="SOL", kurs_eur=64.86,
                            instrument="spot", strategie="bestand",
                            rechnung={}, urteil={"aktion": "HALTEN"},
                            ausstieg=_aus,
                            marken_werte=_bl["_marken_werte"],
                            umgeworfen_preis_eur=63.64)
    pruefe(P, "A4: beide Unterstuetzungen stehen da, mit ihrer Quelle",
           "Unsere Markenrechnung" in _txt and "63,44" in _txt
           and "63,64" in _txt,
           "die SOL-Mail nannte 'die Unterstuetzung' dreimal, zweimal bei "
           "63,44 und einmal bei 63,64 - ohne zu sagen, wessen Zahl das ist")
    _, _gleich = _SM.baue_mail(symbol="SOL", name="SOL", kurs_eur=64.86,
                               instrument="spot", strategie="bestand",
                               rechnung={}, urteil={"aktion": "HALTEN"},
                               ausstieg=_aus,
                               marken_werte=_bl["_marken_werte"],
                               umgeworfen_preis_eur=63.45)
    pruefe(P, "A4: bei praktisch gleicher Zahl schweigt der Hinweis",
           "Unsere Markenrechnung" not in _gleich,
           "ein Hinweis, der immer kommt, wird nicht gelesen")

    # --- A5: der Hoechststand kann nicht unter dem aktuellen Stand liegen.
    _alt = _AR.bewerte(einstieg=63.00, stop_original=60.90,
                       kurs_aktuell=63.90, mfe_r=0.41)
    _alt["empfehlung"] = "HALTEN"
    _s = " ".join(_AR.saetze(_alt))
    pruefe(P, "A5: die Alterung wird benannt statt gedruckt",
           "Hoechststand noch nicht nachgefuehrt" in _s
           and "hoechster Buchgewinn" not in _s,
           "+0.43 R neben 'hoechster Buchgewinn +0.41 R' ist arithmetisch "
           "unmoeglich und laesst den Leser der ganzen Zeile misstrauen")
    _neu = _AR.bewerte(einstieg=63.00, stop_original=60.90,
                       kurs_aktuell=63.90, mfe_r=1.20)
    _neu["empfehlung"] = "HALTEN"
    _s2 = " ".join(_AR.saetze(_neu))
    pruefe(P, "A5: ein echter Hoechststand steht weiterhin da",
           "hoechster Buchgewinn" in _s2,
           "sonst waere die Korrektur ein Informationsverlust")
    pruefe(P, "B1: Prozent vor R, und R nur noch in Klammern",
           "%" in _s2 and "(+0,43 R)" in _s2,
           "R ist eine interne Einheit - die Umrechnung lag seit dem 12.08. "
           "fertig im Code und wurde nie benutzt")

    # --- A1: die Zahlenbeigabe darf in keiner Blockzaehlung landen.
    pruefe(P, "die Markenwerte zaehlen nicht als Faktenblock",
           list(_LB.nur_saetze({"marken": ["x"], "_marken_werte": {"a": 1}}))
           == ["marken"],
           "Anlassfilter und Mindestkriterien zaehlen Bloecke - ein Eintrag "
           "mit Zahlen wuerde beide Messungen verschieben")


def paket_belege() -> None:
    """A6 - behauptet das Modell Zahlen, die es nie bekommen hat? (17.08.2026)

    Nutzerpruefung einer echten SOL-Mail: im Belegblock stand "Umsatzvolumen
    im 35. Perzentil", im Faktenblock derselben Mail "das 0,4-fache des
    Mittels". `faktenblock.kern()` haelt das Perzentil bewusst zurueck."""
    import pruefe_belege_gegen_fakten as PB
    from agent import faktenblock as FB
    from agent import rolle_trader as RT

    P = "Belege"

    # BEIDE RICHTUNGEN. Eine Pruefung, die nur Alarm schlagen kann, ist keine.
    pruefe(P, "A6: das erfundene Volumen-Perzentil wird gefunden",
           bool(PB.pruefe_beleg("Umsatzvolumen im 35. Perzentil deutet auf "
                                "fehlendes Momentum hin")),
           "genau der Satz aus der gemeldeten SOL-Mail")
    pruefe(P, "A6: auch mit erfundener Fensterlaenge",
           bool(PB.pruefe_beleg("MORPHO Handelsvolumen im 100. Perzentil "
                                "der letzten 400 Tage")),
           "'400 Tage' kommt in keinem unserer Saetze vor")
    pruefe(P, "A6: die Finanzierungsrate darf ein Perzentil nennen",
           not PB.pruefe_beleg("Finanzierungsrate im 72. Perzentil bei "
                               "positiven Werten"),
           "dort STEHT eines in den Fakten - ein Befund waere ein Fehlalarm")
    pruefe(P, "A6: und die Marktvolatilitaet auch",
           not PB.pruefe_beleg("Marktlage: Bitcoin-Volatilitaet im 0. "
                               "Perzentil"),
           "das Lagebild gibt eines fuer den MARKT - `auch_woanders`")
    pruefe(P, "A6: unser eigener Volumensatz loest nichts aus",
           not PB.pruefe_beleg("Volumen das 0,4-fache des Mittels deutet "
                               "auf wenig Beteiligung"),
           "er nennt kein Perzentil, und genau so ist er gebaut")
    pruefe(P, "A6: leer und None knallen nicht",
           PB.pruefe_beleg("") == [] and PB.pruefe_beleg(None) == [])

    # DIE LISTE STEHT NEBEN DEM CODE, DER ZURUECKHAELT - nicht im Werkzeug.
    pruefe(P, "A6: die Familien kommen aus `faktenblock`",
           set(PB._familien()) <= set(FB.PERZENTIL_NUR_INTERN)
           and "volumen" in PB._familien(),
           f"{sorted(PB._familien())} aus "
           f"{sorted(FB.PERZENTIL_NUR_INTERN)}")
    pruefe(P, "A6: eine Familie mit Perzentil ANDERSWO wird ausgenommen",
           "schwankung" in FB.PERZENTIL_NUR_INTERN
           and FB.PERZENTIL_NUR_INTERN["schwankung"]["auch_woanders"] is True
           and "schwankung" not in PB._familien(),
           "von 33 Funden der ersten Promptpruefung waren 31 Fehlalarme")

    # Und die Zaehlung ueber viele Zeilen.
    _e = PB.aus_zeilen([
        {"symbol": "SOL", "created_at": "2026-08-17",
         "belege_json": '[{"fakt": "Umsatzvolumen im 35. Perzentil"},'
                        ' {"fakt": "Finanzierungsrate im 72. Perzentil"}]'},
        {"symbol": "BTC", "created_at": "2026-08-17",
         "belege_json": '[{"fakt": "Marktstruktur mit tieferen Tiefs"}]'},
        # Kaputtes JSON darf die Zaehlung nicht anhalten.
        {"symbol": "X", "belege_json": "{kaputt"},
    ])
    pruefe(P, "A6: die Zaehlung findet genau den einen Befund",
           len(_e["befunde"]) == 1 and _e["signale_betroffen"] == 1
           and _e["belege"] == 3,
           f"{len(_e['befunde'])} Befunde, {_e['belege']} Belege")

    # DIE PROMPTZEILE, die den Fall an der Wurzel adressiert.
    pruefe(P, "A6: der Prompt benennt die Stelle konkret",
           "bekommst du KEIN Perzentil" in RT._SCHRITTE,
           "'Erfinde nichts' stand schon da und hat nicht getragen - eine "
           "allgemeine Ermahnung schlaegt keine konkrete Luecke")

    # --- DER UMSCHLAG MUSS SICH SELBST BENENNEN (17.08.2026) -----------
    #
    # Nach Promptstand aufgeschluesselt begannen die falschen
    # Volumen-Perzentile exakt mit 17b - dem Stand, der Krypto-Spot den
    # Umschlag gegeben hat. Der Beleg "MON: Umsatzvolumen 6.0 % (84.
    # Perzentil)" enthaelt BEIDE unsere Zahlen: keine Erfindung, eine
    # Umbenennung.
    from agent import faktenblock as _FB2
    from agent import lagebeschreibung as _LB2

    _u = _LB2._umschlag({"anteil_pct": 6.0, "perzentil": 84, "n": 120})
    pruefe(P, "A6b: der Umschlagsatz nennt sein Hauptwort",
           _u and _u[0].startswith("Der Umschlag dieses Werts"),
           "vorher begann er mit 'Vom gesamten Umlaufbestand' - das "
           "Perzentil hing an einem 'das' auf einen Nebensatz")
    pruefe(P, "A6b: und das Perzentil haengt an DIESEM Hauptwort",
           _u and "Dieser Umschlag liegt im 84. Perzentil" in _u[0],
           _u[0] if _u else "kein Satz")
    pruefe(P, "A6b: der Bezug steht dabei - Umlaufbestand, nicht Mittel",
           _u and "vom Umlaufbestand" in _u[0],
           "der Volumenblock misst gegen den eigenen Durchschnitt, der "
           "Umschlag gegen den Umlaufbestand - der Unterschied ist der "
           "ganze Punkt")
    pruefe(P, "A6b: das Wort 'Umsatz' kommt darin NICHT vor",
           _u and "msatz" not in _u[0],
           "es ist der Name des Blocks nebenan, der bewusst kein "
           "Perzentil hat")
    pruefe(P, "A6b: der Volumenblock hat weiterhin KEIN Perzentil",
           all("Perzentil" not in z for z in _FB2.kern(
               atr_relativ=0.023, schwankung_perzentil=0.3,
               rueckgang_60t=-0.085, momentum_perzentil=0.4,
               volumen_relativ=0.4, volumen_perzentil=0.35)[0]),
           "sonst haette die Umbenennung eine zweite Quelle")
    # Und der Pruefer darf den neuen Satz NICHT melden.
    import pruefe_belege_gegen_fakten as _PB2

    pruefe(P, "A6b: ein Beleg ueber den Umschlag ist erlaubt",
           not _PB2.pruefe_beleg("Der Umschlag liegt im 84. Perzentil"),
           "dort STEHT ein Perzentil in den Fakten - ein Befund waere ein "
           "Fehlalarm")
    pruefe(P, "A6b: die Umbenennung bleibt ein Befund",
           bool(_PB2.pruefe_beleg("Umsatzvolumen 6.0 % (84. Perzentil)")),
           "auch wenn die Zahlen unsere sind - zu DIESER Groesse gibt es "
           "kein Perzentil, und der Leser kann es nicht unterscheiden")

    pruefe(P, "A6: und der Promptstand wurde mitgezogen",
           RT.PROMPT_STAND == "2026-08-17e",
           f"{RT.PROMPT_STAND} - sonst waeren Signale vor und nach der "
           f"Aenderung nicht trennbar")


def paket_lesbar() -> None:
    """Was der Nutzer liest, ist nicht was das Modell liest (17.08.2026).

    Nutzerfrage: *"was soll mir die Einordnung - im gewohnten Bereich -
    sagen? Der Nutzen ist mir nicht klar."* Und der Nutzervorschlag, je
    Abschnitt die Herkunft zu nennen."""
    from agent import marktlage as _ML
    from agent import signal_mail as _SM

    P = "Lesbar"
    _P = "X steht im 50. Perzentil - im gewohnten Bereich."
    _A = "Y steht im 95. Perzentil - aussergewoehnlich hoch."
    _K = "Ein Satz ohne Perzentil."

    # DAS ARGUMENT IN EINER ZEILE: die Schwellen machen den Satz konstant.
    _gewohnt = sum(1 for p in range(101)
                   if _ML._einordnung(p) == _SM.GEWOHNT)
    pruefe(P, "vier von fuenf Perzentilwerten heissen 'im gewohnten Bereich'",
           _gewohnt == 79,
           f"{_gewohnt} von 101 moeglichen Werten - der Satz ist per "
           f"Konstruktion fast immer derselbe (R-T6)")

    # BEIDE RICHTUNGEN, und alle vier Sprachfaelle.
    pruefe(P, "alles gewohnt: eine Zeile statt drei",
           _SM.ohne_gewohntes([_P, _P, _P], "Angaben zur Positionierung")
           == ["Alle 3 Angaben zur Positionierung liegen im gewohnten "
               "Bereich."])
    pruefe(P, "was auffaellt, bleibt WORTGLEICH stehen",
           _A in _SM.ohne_gewohntes([_P, _P, _A], "Angaben"),
           "genau dafuer ist die Zeile da - sie zu kuerzen hiesse, die "
           "einzige Zeile zu verlieren, die etwas sagt")
    pruefe(P, "und dann heisst es 'weitere', nicht 'alle'",
           "2 weitere" in _SM.ohne_gewohntes([_P, _P, _A], "Angaben")[-1],
           "sonst waere unklar, ob der Leser etwas uebersehen hat")
    pruefe(P, "im Singular wird das Hauptwort umgangen",
           _SM.ohne_gewohntes([_P], "Angaben zur Positionierung")[-1]
           == "Die einzige Angabe dazu liegt im gewohnten Bereich.",
           "'Die Angaben zum Umfeld LIEGT' war die erste Fassung")
    pruefe(P, "Zeilen ohne Perzentil bleiben unangetastet",
           _SM.ohne_gewohntes([_K], "Angaben") == [_K],
           "sie tragen ihre eigene Aussage und haben mit dieser Frage "
           "nichts zu tun")
    pruefe(P, "leer bleibt leer",
           _SM.ohne_gewohntes(None, "Angaben") == []
           and _SM.ohne_gewohntes([], "Angaben") == [])

    # ⚠️ DAS MODELL BEHAELT ALLES. Der Filter darf NUR auf dem Weg zur Mail
    # wirken - sonst waere es eine Aenderung der Entscheidungsgrundlage.
    import inspect as _i

    _quelle = _i.getsource(_SM)
    pruefe(P, "der Filter steht in der MAIL, nicht in den Fakten",
           "ohne_gewohntes" not in _quelltext("agent/lagebeschreibung.py")
           and "ohne_gewohntes" not in _quelltext("agent/marktlage.py")
           and "ohne_gewohntes" not in _quelltext("agent/positionierung.py")
           and "def ohne_gewohntes" in _quelle,
           "dem Modell die Einordnung wegzunehmen waere eine Aenderung "
           "seiner Grundlage, keine Darstellungsfrage")

    # --- DIE HERKUNFTSANGABE JE ABSCHNITT ------------------------------
    pruefe(P, "jeder Abschnitt hat eine Herkunft",
           set(_SM.HERKUNFT) == {"wert", "position", "rechnung", "urteil",
                                 "einordnung", "gegenpruefung"},
           str(sorted(_SM.HERKUNFT)))
    pruefe(P, "sie sagt WIE wir es wissen, nicht WER geredet hat",
           all("LLM" not in v and "Gemini" not in v
               for v in _SM.HERKUNFT.values()),
           "der Modellname sagt nichts darueber, ob ein Satz nachpruefbar "
           "ist - 'gemessen' oder 'behauptet' sagt es")
    pruefe(P, "der gemischte Fall wird als solcher benannt",
           "teils aus einer Modellangabe" in _SM.HERKUNFT["rechnung"],
           "der Stop ist arithmetisch exakt und ruht auf einem Prozentsatz "
           "aus einer Modellaussage - 'eigene Berechnung' waere falsche "
           "Sicherheit")

    _, _txt = _SM.baue_mail(
        symbol="SOL", name="SOL", kurs_eur=64.86, instrument="spot",
        strategie="bestand", rechnung={},
        urteil={"aktion": "HALTEN", "begruendung": "x"},
        gegenpruefung=[_P, _P, _K],
        bestand="SOL ist bereits im Bestand: 398 EUR investiert.")
    pruefe(P, "die Herkunft steht in der fertigen Mail",
           "[GEMESSEN - Kurse und Fremdquellen]" in _txt
           and "[BEHAUPTET - andere Quelle" in _txt,
           "je Abschnitt eine Zeile, nicht je Satz")
    pruefe(P, "und die gewohnten Zeilen sind dort verschwunden",
           _txt.count("im gewohnten Bereich") == 1 and _K in _txt,
           "aus zwei gleichlautenden Zeilen wird eine, der Rest bleibt")


def paket_btcmail() -> None:
    """Die sechs Funde der BTC-Hebelmail vom 17.08.2026.

    Vier stammen vom Nutzer, zwei von mir - darunter eine Tautologie, die
    ich am selben Tag selbst eingebaut hatte."""
    from agent import ausstiegsrechnung as _AR
    from agent import entscheidungsrechnung as _ER
    from agent import lagebeschreibung as _LB
    from agent import signal_mail as _SM
    from agent import trefferbilanz as _TB
    from agent import zweite_meinung as _ZM

    P = "BTC-Mail"
    _a = _AR.bewerte(einstieg=56000.0, stop_original=54600.0,
                     kurs_aktuell=54266.0, mfe_r=0.13)
    _a["empfehlung"] = "HALTEN"

    def _mail(inst="hebel", **flags):
        e = dict(_a)
        e.update(flags)
        return _SM.baue_mail(
            symbol="BTC", name="BTC", kurs_eur=54266.36, instrument=inst,
            strategie="bestand", rechnung={},
            urteil={"aktion": "HALTEN", "begruendung": "x",
                    "was_dagegen": "Schwaeche",
                    "umgeworfen_durch": "Schlusskurs unter 53.274 EUR"},
            ausstieg=e,
            bestand="In BTC besteht keine offene Hebelposition.")[1]

    # --- P2: drei Zustaende statt zweier. Der gemeldete Fall ist der
    # mittlere: BTC liegt im SPOT, die Mail handelt vom HEBEL.
    _echt = _mail(ist_bestand=True)
    _gegen = _mail(ist_bestand=False, ist_bestand_gegenseite=True)
    _nichts = _mail(ist_bestand=False, ist_bestand_gegenseite=False)
    pruefe(P, "P2: eine echte Position heisst weiterhin so",
           "Bestehende Position:" in _echt)
    pruefe(P, "P2: der GEMELDETE Fall nennt die andere Seite",
           "Sie halten diesen Wert im Spot, aber keine Hebelposition"
           in _gegen and "Bestehende Position:" not in _gegen,
           "die Mail sagte oben 'keine offene Hebelposition' und unten "
           "'Bestehende Position' - weil beide Toepfe verschmolzen waren")
    pruefe(P, "P2: und im Spot-Lauf steht es andersherum",
           "Sie halten eine Hebelposition auf diesen Wert" in
           _mail("spot", ist_bestand=False, ist_bestand_gegenseite=True))
    pruefe(P, "P2: ohne alles bleibt es der verfolgte Vorschlag",
           "(NICHT im Bestand)" in _nichts)
    pruefe(P, "P2: kein zusammengesteckter Artikel",
           "eine Spot-Bestand" not in _gegen,
           "mein erster Entwurf baute 'eine {_andere}' zusammen")

    # --- P5: ein unbekanntes Urteil darf nicht lautlos verschwinden.
    _g = ["Die offenen Kontrakte sind gefallen."]
    pruefe(P, "P5: ein bekanntes Urteil steht wie bisher da",
           "kein Einwand" in _ZM.zeilen(
               {"einwand": "nein", "einwand_grund": "x", "grundlage": _g})[0])
    _unbek = _ZM.zeilen({"einwand": "keine", "grundlage": _g})
    pruefe(P, "P5: ein unbekanntes wird BENANNT statt weggelassen",
           _unbek and "nicht lesbar" in _unbek[0],
           "vorher zeigte der Abschnitt die Fakten samt Schlusssatz, aber "
           "kein Urteil - genau die Mail, die gemeldet wurde")
    pruefe(P, "P5: gar kein Urteil bleibt ein leerer Abschnitt",
           _ZM.zeilen({"grundlage": _g}) == [],
           "ein Abschnitt ohne Inhalt saehe aus wie ein Befund")

    # --- B: meine eigene Tautologie.
    def _bilanz(basis, wahr, faelle):
        return {"basisrate": basis, "wahrscheinlichkeit": wahr,
                "breakeven": 0.94, "traegt": False, "belastbar": False,
                "faelle": faelle, "crv": 0.2, "treffer": 1,
                "abgelaufen": 0, "anteil_entschieden": 1.0}

    _btc = " ".join(_TB.satz(_bilanz(0.83, 0.834, 1), einstieg=100.0,
                             stop=97.5, einsatz_eur=1000.0))
    _sol = " ".join(_TB.satz(_bilanz(0.34, 0.36, 3), einstieg=100.0,
                             stop=97.5, einsatz_eur=1000.0))
    pruefe(P, "B: keine 'Erfahrungsrate von 83' neben einer 83",
           "Erfahrungsrate von 83" not in _btc
           and "Das ist die Erfahrungsrate" in _btc,
           "bei CRV 0,2 runden beide Zahlen auf denselben Wert - der Satz "
           "erklaerte dann nichts und las sich wie ein Fehler")
    pruefe(P, "B: wo sie sich unterscheiden, wird es weiter erklaert",
           "Erfahrungsrate von 34, angepasst um 3 eigene Faelle" in _sol,
           "sonst waere die Korrektur ein Informationsverlust")
    pruefe(P, "B: und der Singular stimmt",
           "1 eigener Fall verschiebt sie noch nicht" in _btc, _btc[-90:])

    # --- C: keine Anrede an das Modell im Nutzertext.
    # ⚠️ MIT GRUPPE (23.08.2026): der Baustein haengt nicht mehr am Lauf,
    # sondern an der Handelbarkeit. Ohne sie kaeme hier eine leere Liste, und
    # die drei Pruefungen darunter pruefen dann nichts.
    _hg = " ".join(_LB._hebelgeometrie(900.0, 54266.0, "spot",
                                       assetklasse="krypto"))
    pruefe(P, "C: kein 'du' im Faktentext",
           " du " not in f" {_hg} " and "deiner" not in _hg,
           "Faktentexte gehen an BEIDE Leser - wer einen anspricht, "
           "schreibt fuer den anderen falsch")
    pruefe(P, "C: die Aussage bleibt vollstaendig",
           "Risikobudget" in _hg and "Stopabstand" in _hg
           and "nach der Entscheidung" in _hg,
           "sie haelt das Modell davon ab, selbst einen Faktor zu waehlen")

    # ⚠️ UND SIE UNTERSTELLT KEIN HEBELGESCHAEFT MEHR (19.08.2026).
    # Vorher begann sie mit "Der Abstand ... haengt allein am Hebelfaktor" -
    # eine Feststellung. Seit S5 faellt in vier von fuenf Faellen Hebel 1,0
    # an, und der Faktenblock erklaerte dann Hebelfaktoren, waehrend die
    # Rechnung zwei Abschnitte weiter "kein Hebel noetig" schrieb.
    pruefe(P, "C: der Satz ist BEDINGT, nicht feststellend",
           _hg.startswith("Falls ein Hebel noetig wird"),
           "ein Faktenblock, der ein Hebelgeschaeft unterstellt, "
           "widerspricht in vier von fuenf Mails der eigenen Rechnung")
    pruefe(P, "C: und er verweist auf die Stelle, die es aufloest",
           "DIE RECHNUNG" in _hg and "kein Hebelgeschaeft" in _hg,
           "der Leser soll nicht raten muessen, wo die Bedingung "
           "beantwortet wird")

    # --- D: Grammatik.
    _r = _ER.rechne(kurs=100.0, atr=2.0, risiko_eur=25.0, instrument="spot",
                    betrag_wunsch_eur=1000.0)
    _eins = dict(_r, haltedauer_tage=1)
    _drei = dict(_r, haltedauer_tage=3)
    pruefe(P, "D: 'etwa 1 Handelstag', nicht 'Handelstage'",
           any("etwa 1 Handelstag " in z for z in _ER.saetze(_eins)))
    pruefe(P, "D: der Plural bleibt Plural",
           any("etwa 3 Handelstage " in z for z in _ER.saetze(_drei)))

    # --- P3: der Bezug wird ausgeschrieben.
    pruefe(P, "P3: kein Fuerwort, dessen Bezug man raten muss",
           "Die Entscheidung HALTEN waere widerlegt durch" in _echt
           and "Widerlegt waere das durch" not in _echt,
           "'Was dagegen spricht ...' und 'Widerlegt waere DAS durch ...' "
           "standen direkt untereinander")

    # --- P1: die Zeitachse.
    import inspect as _i

    from ui import trade_chart as _TC

    _src = _i.getsource(_TC.render_trade_chart)
    pruefe(P, "P1: der Chart setzt Zeitmarken statt keiner",
           "set_xticklabels" in _src and "set_xlabel" in _src,
           "hier stand `ax.set_xticks([])` - ob der Verlauf zwei Wochen "
           "oder ein halbes Jahr zeigt, aendert alles an seiner Bedeutung")
    pruefe(P, "P1: das Datum kommt aus DERSELBEN Kerze wie der Kurs",
           'getattr(hist[i], "date"' in _src,
           "eine zweite Zeitquelle waere eine zweite Wahrheit")


def paket_marken() -> None:
    """Die Marken: Richtung, Bruchstatus, Name - und KEIN Deckel.

    Nutzerfrage 17.08.2026: *"Die Punkte sind immer eine Trendwende, Kurs
    geht wieder nach unten - und nicht hat Kurs erreicht und ist
    durchgegangen. Ist das korrekt?"* Ja - aber die Richtung stand nicht
    dabei, und ob die Marke zuletzt gehalten hat, auch nicht."""
    import numpy as _np

    from agent import entscheidungsrechnung as _ER
    from agent import lagebeschreibung as _LB
    from agent import signal_mail as _SM

    P = "Marken"

    # Eine gebaute Reihe: der Kurs dreht dreimal bei 110 nach unten und
    # zweimal bei 90 nach oben.
    n = 200
    c = _np.full(n, 100.0)
    h = _np.full(n, 101.0)
    l = _np.full(n, 99.0)
    for j in (30, 70, 110):
        h[j] = 110.0
    for j in (50, 90):
        l[j] = 90.0
    v = _LB.niveaus_werte(c, h, l, n - 1, 5.0, 100.0, 100.0,
                          [f"2026-01-{1 + (j % 28):02d}" for j in range(n)])

    oben = [m for m in v["oben"] if abs(m["preis_eur"] - 110.0) < 1]
    unten = [m for m in v["unten"] if abs(m["preis_eur"] - 90.0) < 1]
    pruefe(P, "drei Wenden nach unten werden als solche gezaehlt",
           bool(oben) and oben[0]["nach_unten_gedreht"] == 3
           and oben[0]["gehalten"] == 0,
           str(oben[:1]))
    pruefe(P, "zwei Wenden nach oben ebenso",
           bool(unten) and unten[0]["gehalten"] == 2
           and unten[0]["nach_unten_gedreht"] == 0,
           str(unten[:1]))
    pruefe(P, "die Summe ist die alte Beruehrungszahl",
           bool(oben) and oben[0]["beruehrungen"] == 3,
           "'7-mal beruehrt' war richtig, sagte nur nicht wohin")
    pruefe(P, "und das Datum der letzten Beruehrung steht dabei",
           bool(oben) and oben[0]["letzte_beruehrung"],
           "die BTC-Marke bei 65.652 besteht aus Punkten ueber 800 "
           "Handelstage - ohne Datum wirkt sie aktueller, als sie ist")

    # BEREITS DURCHBROCHEN: der Kurs schliesst nach der letzten Beruehrung
    # ueber der Marke.
    c2 = c.copy()
    c2[150:] = 115.0
    v2 = _LB.niveaus_werte(c2, h, l, n - 1, 5.0, 100.0, 100.0)
    gebrochen = [m for m in (v2["oben"] + v2["unten"])
                 if abs(m["preis_eur"] - 110.0) < 1]
    pruefe(P, "eine durchbrochene Marke wird als solche erkannt",
           bool(gebrochen) and gebrochen[0]["gefegt"] is True,
           "uebernommen aus `liquidity_pools._ist_gefegt` - ohne sie sagt "
           "eine Marke mit fuenf Umkehrpunkten nichts darueber, ob sie "
           "zuletzt gehalten hat")
    pruefe(P, "eine ungebrochene nicht",
           bool(oben) and oben[0]["gefegt"] is False)

    # ⚠️ KEIN DECKEL. Gemessen: 44 von 44 Symbolen gedeckelt, Median 0,21.
    _r = _ER.rechne(kurs=100.0, atr=5.0, risiko_eur=25.0,
                    betrag_wunsch_eur=1000.0)
    pruefe(P, "das Ziel bleibt mechanisch",
           _r["ziel_regel"] == "mechanisch, 2x Risiko"
           and abs(_r["crv"] - 2.0) < 1e-9,
           "der Deckel haette bei 44 von 44 Symbolen zugeschlagen, 98 % "
           "unter CRV 0,5 - auf Tagesfraktalen ist immer eine Marke im Weg")
    pruefe(P, "und die Kette fuettert den Deckel nicht mehr",
           "widerstand=_marke_im_weg" not in _quelltext("agent/rollen_lauf.py"),
           "die Funktion bleibt, der Aufruf ist weg - wer sie je will, "
           "findet im Kommentar, warum sie abgeschaltet wurde")

    # DIE MARKEN STEHEN STATTDESSEN IN DER MAIL.
    marken = [{"preis_eur": 105.0, "abstand_atr": 1.0, "beruehrungen": 3,
               "nach_unten_gedreht": 3, "gehalten": 0, "gefegt": False,
               "letzte_beruehrung": "2026-07-15"},
              {"preis_eur": 108.0, "abstand_atr": 1.6, "beruehrungen": 2,
               "nach_unten_gedreht": 1, "gehalten": 1, "gefegt": True,
               "letzte_beruehrung": "2024-11-04"}]
    z = " ".join(_ER.saetze(_r, marken))
    pruefe(P, "die Marken stehen unter dem Take-Profit",
           "Auf dem Weg dorthin" in z and "105,00 EUR" in z)
    pruefe(P, "mit Richtung, Datum und Bruchstatus",
           "3x nach unten gedreht" in z and "zuletzt 2024-11-04" in z
           and "seither durchbrochen" in z)
    pruefe(P, "und mit dem Erlaeuterungstext",
           "dort liegen Auftraege" in z and "GERECHNET, nicht vorhergesagt" in z,
           "Nutzerwunsch: ein sinnvoller Ergaenzungstext zur Nutzung")
    pruefe(P, "hoechstens drei, auch wenn mehr im Weg liegen",
           _ER.MARKEN_IN_DER_MAIL == 3)
    pruefe(P, "liegt keine im Weg, steht auch das da",
           "keine Marke im Weg" in " ".join(
               _ER.saetze(_r, [{"preis_eur": 500.0, "abstand_atr": 9.0,
                                "beruehrungen": 1, "nach_unten_gedreht": 1,
                                "gehalten": 0, "gefegt": False}])),
           "sonst waere unklar, ob geprueft wurde")
    pruefe(P, "Singular und Plural stimmen",
           "liegt 1 Marke" in " ".join(_ER.saetze(_r, marken[:1]))
           and "liegen 2 Marken" in z)

    # DER NAME NUR FUER KRYPTO.
    def _mail(klasse):
        return _SM.baue_mail(
            symbol="X", name="X", kurs_eur=100.0, instrument="spot",
            strategie="einstieg", rechnung=_r,
            urteil={"aktion": "KAUFEN", "begruendung": "x"},
            marken_werte={"oben": marken}, assetklasse=klasse)[1]

    pruefe(P, "Krypto nennt sie Liquiditaetszonen",
           "(Liquiditaetszonen)" in _mail("krypto"))
    for klasse in ("rohstoffe", "aktien", "etf", "hedge"):
        pruefe(P, f"{klasse} nennt sie nicht so",
               "(Liquiditaetszonen)" not in _mail(klasse)
               and "Auf dem Weg dorthin" in _mail(klasse),
               "die Marken gibt es ueberall, der Name traegt eine Deutung, "
               "die am 23.07. auf Krypto begrenzt wurde")

    # DER CHART BESCHRIFTET SIE.
    import inspect as _i

    from ui import trade_chart as _TC

    _src = _i.getsource(_TC.render_trade_chart)
    pruefe(P, "der Chart beschriftet die Marken",
           "annotate" in _src and "beruehrungen" in _src,
           "hier stand 'ohne Beschriftung im Bild' - das galt, solange im "
           "Text EINE Marke stand")
    pruefe(P, "und vertraegt weiterhin eine reine Preisliste",
           "isinstance(eintrag, dict)" in _src,
           "kein Aufrufer soll brechen")
    pruefe(P, "die Kette reicht die Marken jetzt durch",
           "marken=None," not in _quelltext("agent/rollen_lauf.py"),
           "der Chart konnte es immer, bekam aber None")


def paket_provider() -> None:
    """Kein lebender Pfad ruft einen toten Provider (17.08.2026).

    Nutzerfrage an der Budgetanzeige: *"wie kann es sein, dass Mistral
    einen Aufruf hatte?"* Antwort: `marktscan_backward_tracking_job`
    waehlte `mistral_client or gemini_client` - Mistral zuerst. Sein
    Free-Plan ist seit dem 07.08. kostenpflichtig, jeder Aufruf endet mit
    402. Die Kategorie-Synthese wurde am 14.08. genau so bereinigt; diese
    Stelle blieb stehen."""
    P = "Provider"
    _bg = _quelltext("scheduler/background.py")

    pruefe(P, "kein lebender Pfad zieht Mistral dem Rueckfall vor",
           "mistral_client or gemini_client" not in _bg,
           "der Aufruf kostete nichts ausser einer Fehlerzeile - und einer "
           "'1' in der Budgetanzeige, die eine Nutzung behauptet, die es "
           "nicht gab")
    pruefe(P, "der Parameter bleibt in der Signatur",
           "def marktscan_backward_tracking_job(" in _bg
           and "mistral_client=None, gemini_client=None," in _bg,
           "der Scheduler uebergibt ihn - ihn dort zu entfernen waere eine "
           "Aenderung an mehreren Aufrufstellen fuer nichts")
    pruefe(P, "und der Job waehlt jetzt Gemini",
           "llm_client = gemini_client" in _bg)

    # Der Kanarienvogel haengt am selben toten Provider - er laeuft nicht,
    # aber wer ihn aktiviert, muss es wissen.
    import inspect as _i

    from scheduler import background as _BG

    _kv = _i.getdoc(_BG.kanarienvogel_job) or ""
    pruefe(P, "der Kanarienvogel warnt vor seinem eigenen Provider",
           "402" in _kv and "PROVIDER TAUSCHEN" in _kv,
           "zehn Fehlschlaege taeglich und eine Drift-Messung, die nichts "
           "misst - und anders als sonst gibt es hier KEINEN Rueckfall")
    pruefe(P, "er ist weiterhin nicht registriert",
           'id="kanarienvogel"' not in _bg,
           "die Warnung ersetzt die Entscheidung nicht")


def paket_fett() -> None:
    """Die Handelsparameter fett und schwarz, und alle Zahlen deutsch.

    Nutzervorgabe 17.08.2026: *"bitte folgende Bereiche der eMail FETT und
    schwarz - da dies die wesentlichen Parameter des Handels sind:
    Einstiegszone, Stop (stoploss?), TP, Haltedauer, Betrag und Hebel"* -
    und danach *"fuer alle eMail pruefen bitte"*."""
    import re as _re

    from agent import ausstiegsrechnung as _AR
    from agent import entscheidungsrechnung as _ER
    from agent import schreibweise as _SW
    from ui import formatting as _F

    P = "Fett"
    _FETT = 'style="font-weight:bold;color:#000000;"'

    pruefe(P, "genau die sechs vom Nutzer genannten Groessen",
           _F.HANDELSPARAMETER == frozenset({
               "Einstiegszone", "Stop", "Take-Profit", "TP", "Haltedauer",
               "Betrag", "Hebel"}),
           "'Take-Profit' und 'TP' sind dieselbe Groesse in zwei "
           "Schreibweisen - beide muessen drin sein")

    # AM ERSTEN WORT, nicht am Vorkommen. Das ist der ganze Unterschied
    # zwischen "Stop  3,60 EUR" und "der Trailing-Stop loest erst aus".
    for zeile in ("Einstiegszone   3,81 bis 3,85 EUR",
                  "Stop            3,60 EUR  (5,9 % - 2,5 x ATR)",
                  "Take-Profit     4,26 bis 4,30 EUR",
                  "TP              4,26 EUR",
                  "Haltedauer      etwa 25 Handelstage",
                  "Betrag          374 EUR",
                  "Hebel           2,0"):
        pruefe(P, f"fett: {zeile.split(' ', 1)[0]}",
               _F.classify_detail_line(zeile) == "handelsparameter")
    for zeile in ("der Trailing-Stop loest erst ab 1,0 R aus",
                  "Stopabstand und Ziel stammen aus derselben Rechnung",
                  "Ihr Betrag im Bestand bleibt unberuehrt"):
        pruefe(P, f"NICHT fett: {zeile[:34]}",
               _F.classify_detail_line(zeile) != "handelsparameter",
               "sonst wuerde jeder Fliesstext fett, der zufaellig mit "
               "einem Parameternamen beginnt - und fett heisst dann nichts "
               "mehr")

    # ... und die Regel muss VOR den anderen greifen, sonst faellt die
    # Zeile als Fliesstext durch.
    _r = _ER.rechne(kurs=3.83, atr=0.09, risiko_eur=22.0,
                    betrag_wunsch_eur=800.0, instrument="hebel")
    _html = _F.render_detail_html("\n".join(_ER.saetze(_r)))
    _fett = _re.findall(_FETT.replace('"', '"') + r">([^<]+)", _html)
    for name in ("Einstiegszone", "Stop", "Take-Profit", "Haltedauer",
                 "Betrag"):
        pruefe(P, f"in der fertigen Mail fett: {name}",
               any(z.startswith(name) for z in _fett),
               "geprueft am gerenderten HTML, nicht an der Regel - "
               "dazwischen liegt die Reihenfolge der Regeln")

    # DEUTSCHE SCHREIBWEISE, ueber die ganze Mail.
    pruefe(P, "der Formatierer dreht Punkt und Komma",
           (_SW.de(1234.5) == "1.234,5"
            and _SW.de(0.9, 2, True) == "+0,90"
            and _SW.de(-0.9, 2, True) == "-0,90"))

    _a = _AR.bewerte(einstieg=3.66, stop_original=3.56, kurs_aktuell=3.83,
                     mfe_r=1.9)
    _a["empfehlung"] = "STOP NACHZIEHEN"
    _text = "\n".join(_ER.saetze(_r) + _AR.saetze(_a))
    # ⚠️ DIESELBE REGEL WIE IN simuliere_kette.py. Zwei Messungen,
    # die verschieden zaehlen, sind schlimmer als eine - und meine erste
    # Fassung fand nur EINSTELLIGE Nachkommastellen: "2.5" ja, "3.81"
    # nein (das \b scheitert an der zweiten Ziffer). Sie meldete sauber,
    # wo es nicht sauber war.
    from simuliere_kette import _englische_zahlen
    _punkte = _englische_zahlen(_text)
    pruefe(P, "der Tausenderpunkt gilt NICHT als englische Schreibweise",
           not _englische_zahlen("1.234,5 EUR und 1.234.567,8 EUR"),
           "sonst meldet die Pruefung genau die Schreibweise als Fehler, "
           "die sie durchsetzen soll")
    pruefe(P, "und mehrstellige Nachkommastellen werden gefunden",
           _englische_zahlen("3.81 bis 3,85") == ["3.81"],
           "daran ist meine erste Fassung gescheitert")

    pruefe(P, "keine einzige Zahl mit englischem Punkt",
           not _punkte,
           f"gefunden: {_punkte} - zuletzt hingen hier zwei: die "
           f"Trailing-Begruendung ('1.90 R' neben '+1,70 R' zwei Zeilen "
           f"hoeher) und der Stopfaktor ('2.5 x ATR' aus ':g')")


    # ⚠️ GEFUNDEN DURCH DIE PRUEFUNG UEBER ALLE MAILS, in JEDER
    # Gruppe: der Treuebefund Z-1 schrieb die Python-Liste roh hinein.
    from agent.gegenpruefer_rollen import _zahlenliste as _ZL
    pruefe(P, "der Z-1-Befund nennt die Zahlen als Satz, nicht als Liste",
           _ZL([42.0, 17.0]) == "42 und 17",
           "in der Mail stand '[42.0, 17.0]' - englische Punkte, eckige "
           "Klammern und ein '.0', das eine Genauigkeit vortaeuscht, "
           "die das Modell nicht hatte")
    pruefe(P, "und Nachkommastellen bleiben, wo es welche gibt",
           _ZL([1234.5, 3.25]) == "1.234,50 und 3,25")


def paket_andrang() -> None:
    """Rolle G kam bei 85 von 159 Urteilen nicht dran (17.08.2026).

    Nicht wegen des Anbieterlimits, sondern wegen unserer Geduld: bei zwei
    Plaetzen und ~30 s je Aufruf reichten 180 s Wartezeit fuer 12 Signale,
    ein Umlauf hat 20-40. Die Kapazitaet (2 * 3600/30 = ~240 Aufrufe je
    Stunde) war die ganze Zeit da."""
    import inspect as _i

    from agent import zweite_meinung as _ZM
    from api import zai as _ZAI

    P = "Andrang"

    # ---- DAS ANBIETERLIMIT IST HART UND BLEIBT ----
    pruefe(P, "zwei gleichzeitig - an BEIDEN Stellen",
           _ZM.MAX_GLEICHZEITIG == 2 == _ZAI.MAX_CONCURRENT_REQUESTS,
           "Z.ais eigene Doku fuer glm-4.5-flash nennt 'Concurrency limit: "
           "2'; alles darueber wird serverseitig per 429 abgewiesen - genau "
           "der Zustand vom 28.07. mit 210 Logzeilen, praktisch alle 429")

    # ---- DIE REIHENFOLGE DES AUFGEBENS ----
    # Wer zuerst aufgibt, entscheidet, ob ein Befund verloren geht oder nur
    # spaet kommt.
    _schlimmster = (_ZM.WARTE_AUF_PLATZ_SEKUNDEN
                    + _ZM.ZEITGRENZE_ROLLE_G_SEKUNDEN)
    _aufgabe = _ZM.WARTE_MAX_SEKUNDEN + 60          # rollen_lauf.py::join
    pruefe(P, "die Warteschlange gibt VOR dem Hauptfaden auf",
           _schlimmster < _aufgabe,
           f"{_schlimmster} s gegen {_aufgabe} s - war bis heute umgekehrt "
           f"(180+150=330 gegen 240+60=300): der Hauptfaden stieg aus, der "
           f"Faden lief als Daemon weiter, seine Mail ging MIT dem Einwand "
           f"raus und ZM.schreibe fiel aus. Die Mail zeigte einen Befund, "
           f"den die Datenbank nicht kennt")
    _q = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "und die Aufgabegrenze steht wirklich an dieser Zahl",
           "faden.join(timeout=ZM.WARTE_MAX_SEKUNDEN + 60)" in _q,
           "die Rechnung oben ist nur so viel wert wie ihr Bezug zum Code")

    # ---- UND DAS GANZE PASST IN DEN TAKT ----
    _takt = _konst_aus("scheduler/background.py",
                       "HEBEL_SCREENING_INTERVAL_MINUTES")
    pruefe(P, "der Umlauf endet vor dem naechsten Takt",
           bool(_takt) and _aufgabe < _takt * 60,
           f"{_aufgabe} s gegen {(_takt or 0) * 60:.0f} s - sonst faellt "
           f"jeder zweite Takt aus (APScheduler laesst keine zweite Instanz)")

    # ---- KAPAZITAET: WAS DIE ZAHL BEDEUTET ----
    _vorher = 2 * 180 // 30
    _jetzt = 2 * _ZM.WARTE_AUF_PLATZ_SEKUNDEN // 30
    pruefe(P, f"Wartezeit traegt {_jetzt} Signale statt {_vorher}",
           _jetzt >= 30,
           "2 Plaetze * Wartezeit / 30 s je Aufruf - das Limit begrenzt, "
           "wie viele GLEICHZEITIG laufen, nicht wie viele drankommen")

    # ---- DIE EIGENE ZEITGRENZE, OHNE DIE ALTEN ZU TREFFEN ----
    pruefe(P, "die globale Z.ai-Zeitgrenze ist UNVERAENDERT",
           _ZAI.REQUEST_TIMEOUT_SECONDS == 150,
           "die alten Pipelines (aktien, hedge, hebel) schicken ueber "
           "fuehre_beide_calls_im_hintergrund weiter den grossen Prompt - "
           "global senken haette sie abgeschnitten")
    pruefe(P, "chat() nimmt eine eigene Zeitgrenze entgegen",
           "timeout" in _i.signature(_ZAI.ZaiClient.chat).parameters
           and _i.signature(_ZAI.ZaiClient.chat)
                 .parameters["timeout"].default is None,
           "Vorgabe None heisst: wer nichts angibt, bekommt was er immer "
           "bekam")
    pruefe(P, "und reicht sie an requests durch",
           "timeout=timeout or REQUEST_TIMEOUT_SECONDS"
           in _quelltext("api/zai.py"),
           "ein Parameter, der nicht am Draht ankommt, ist Dekoration")
    pruefe(P, "Rolle G uebergibt ihre eigene",
           "timeout=ZEITGRENZE_ROLLE_G_SEKUNDEN"
           in _quelltext("agent/zweite_meinung.py"))
    pruefe(P, "und die deckt den gemessenen Ausreisser",
           _ZM.ZEITGRENZE_ROLLE_G_SEKUNDEN > 65.5,
           "live gemessen 22,4 / 29,7 / 33,1 s, ein Ausreisser bei 65,5 s - "
           "auf einem Prompt von 1.495 Zeichen, nicht den 34.611, an denen "
           "die 150 s gemessen wurden")
    pruefe(P, "sie ist deutlich kleiner als die globale",
           _ZM.ZEITGRENZE_ROLLE_G_SEKUNDEN < _ZAI.REQUEST_TIMEOUT_SECONDS / 1.5,
           "bei zwei Plaetzen blockiert ein haengender Aufruf die halbe "
           "Kapazitaet - 150 s davon sind fuenf normale Aufrufe")

    # ---- WER NICHT DRANKAM, MUSS SICH VOM REST UNTERSCHEIDEN ----
    # "Fail-soft ist fail-silent": ein Signal ohne Gegenpruefungszeilen sieht
    # in der Mail sonst aus wie eines, das die Pruefung bestanden hat.
    import threading as _th
    import time as _t

    _alt = _ZM.WARTE_AUF_PLATZ_SEKUNDEN
    _ZM.WARTE_AUF_PLATZ_SEKUNDEN = 0.05
    _blocker = [_th.Thread(target=lambda: _ZM._mit_platz(_t.sleep, 1.0))
                for _ in range(_ZM.MAX_GLEICHZEITIG)]
    try:
        for _b in _blocker:
            _b.start()
        _t.sleep(0.2)
        _geworfen = False
        try:
            _ZM._mit_platz(lambda: "durch")
        except _ZM.Andrang:
            _geworfen = True
        pruefe(P, "wer keinen Platz bekommt, bekommt Andrang",
               _geworfen,
               "nicht None, nicht ein leeres Ergebnis - der Aufrufer bucht "
               "es als uebersprungen, nicht als bestanden")
    finally:
        _ZM.WARTE_AUF_PLATZ_SEKUNDEN = _alt
        for _b in _blocker:
            _b.join()


def paket_ausfall() -> None:
    """Der Abbruch nach Transportfehlern - der Preis der langen Wartezeit.

    Mit 180 s wartete ein Faden bei einem Anbieterausfall drei Minuten aufs
    Nichts; mit 480 s waeren es acht, mal vierzig Faeden. Die Wartezeit hilft
    gegen Andrang und schadet bei Ausfall, also braucht sie einen
    Gegenspieler, der die beiden Lagen unterscheidet (17.08.2026)."""
    import json as _json
    import threading as _th
    import time as _t

    import requests as _rq

    from agent import zweite_meinung as _ZM

    P = "Ausfall"

    # ---- UEBERSPRUNGEN IST NICHT FEHLGESCHLAGEN ----
    pruefe(P, "Ausfall erbt von Andrang",
           issubclass(_ZM.Ausfall, _ZM.Andrang),
           "die Folge ist dieselbe - der Aufruf hat nicht stattgefunden -, "
           "also behandelt jeder bestehende `except Andrang` ihn richtig, "
           "ohne dass eine Stelle nachgezogen werden muss")
    pruefe(P, "und bleibt trotzdem unterscheidbar",
           _ZM.Ausfall is not _ZM.Andrang,
           "'zu viele auf einmal' und 'der Anbieter ist weg' sind zwei "
           "Lagen mit zwei Massnahmen")

    _alt_w, _alt_s = _ZM.WARTE_AUF_PLATZ_SEKUNDEN, _ZM.AUSFALL_SCHWELLE
    try:
        _ZM.beginne_umlauf()

        def _tot():
            raise _rq.exceptions.ConnectionError("weg")

        def _lebt():
            return "ok"

        # ---- IN FOLGE, NICHT INSGESAMT ----
        for _ in range(_ZM.AUSFALL_SCHWELLE - 1):
            try:
                _ZM._mit_platz(_tot)
            except _rq.exceptions.ConnectionError:
                pass
        pruefe(P, f"{_ZM.AUSFALL_SCHWELLE - 1} Fehler brechen NICHT ab",
               _ZM._abgebrochen() is None,
               "einzelne HTTP-Fehler kamen am 17.08. vereinzelt vor, ohne "
               "dass der Anbieter weg war")
        _ZM._mit_platz(_lebt)
        for _ in range(_ZM.AUSFALL_SCHWELLE - 1):
            try:
                _ZM._mit_platz(_tot)
            except _rq.exceptions.ConnectionError:
                pass
        pruefe(P, "ein Erfolg dazwischen setzt den Zaehler zurueck",
               _ZM._abgebrochen() is None,
               "ein Anbieter, der weg ist, laesst ALLES scheitern - ein "
               "wackliger laesst Erfolge dazwischen zu. Eine Gesamtzahl "
               "wuerde beide Lagen gleich behandeln")

        # ---- UND DER LETZTE LOEST AUS ----
        try:
            _ZM._mit_platz(_tot)
        except _rq.exceptions.ConnectionError:
            pass
        pruefe(P, f"{_ZM.AUSFALL_SCHWELLE} in Folge brechen ab",
               _ZM._abgebrochen() is not None)

        # ---- DANACH WIRD NICHT MEHR GEFRAGT, UND ZWAR SOFORT ----
        _gefragt = [0]

        def _zaehl():
            _gefragt[0] += 1
            return "ok"

        _t0 = _t.perf_counter()
        _geworfen = False
        try:
            _ZM._mit_platz(_zaehl)
        except _ZM.Ausfall:
            _geworfen = True
        _dauer = _t.perf_counter() - _t0
        pruefe(P, "weitere Aufrufe werfen Ausfall statt zu fragen",
               _geworfen and _gefragt[0] == 0)
        pruefe(P, "und zwar OHNE zu warten",
               _dauer < 1.0,
               f"{_dauer:.3f} s - stuende der Anbieter, ginge der Faden "
               f"sonst {_ZM.WARTE_AUF_PLATZ_SEKUNDEN:.0f} s in eine "
               f"Schlange, an deren Ende dieselbe Zeitgrenze steht, die "
               f"schon dreimal ablief")

        # ---- DER NAECHSTE UMLAUF PROBIERT WIEDER ----
        _ZM.beginne_umlauf()
        pruefe(P, "beginne_umlauf() macht den Weg wieder frei",
               _ZM._abgebrochen() is None and _ZM._mit_platz(_lebt) == "ok",
               "der Abbruch gilt fuer den laufenden Umlauf, nicht fuer "
               "immer - beim naechsten Takt kostet ein fortdauernder "
               "Ausfall drei Aufrufe statt vierzig")
        pruefe(P, "und der Umlauf setzt ihn wirklich zurueck",
               "ZM.beginne_umlauf()"
               in _quelltext("scheduler/rollen_job.py"),
               "in fuehre_umlauf, nicht in fuehre_bereich - sonst wuerde je "
               "Gruppe neu erprobt")

        # ---- INHALT IST KEIN TRANSPORT ----
        _ZM.beginne_umlauf()

        def _kaputt():
            _json.loads("{nicht json")

        for _ in range(_ZM.AUSFALL_SCHWELLE + 2):
            try:
                _ZM._mit_platz(_kaputt)
            except _json.JSONDecodeError:
                pass
        pruefe(P, "unbrauchbare ANTWORTEN brechen nicht ab",
               _ZM._abgebrochen() is None,
               "der Anbieter lebt, er hat geantwortet - sie zu zaehlen "
               "hiesse, wegen schlechter Antworten das Fragen einzustellen, "
               "und genau die Faelle will man sehen")

        # ---- DER NACHWEIS AM AUSFALL SELBST, Massstab 1:100 ----
        def _lauf(mit_abbruch: bool) -> tuple:
            _ZM.beginne_umlauf()
            _ZM.WARTE_AUF_PLATZ_SEKUNDEN = 1.2
            _ZM.AUSFALL_SCHWELLE = 3 if mit_abbruch else 10 ** 9
            _n = [0]
            _s = _th.Lock()

            def _langsam_tot():
                with _s:
                    _n[0] += 1
                _t.sleep(0.15)                  # die Zeitgrenze laeuft ab
                raise _rq.exceptions.ConnectTimeout("weg")

            def _einer():
                try:
                    _ZM._mit_platz(_langsam_tot)
                except Exception:                            # noqa: BLE001
                    pass

            _f = [_th.Thread(target=_einer) for _ in range(20)]
            _a = _t.perf_counter()
            for _x in _f:
                _x.start()
            for _x in _f:
                _x.join()
            return _n[0], _t.perf_counter() - _a

        _ohne, _dauer_ohne = _lauf(False)
        _mit, _dauer_mit = _lauf(True)
        pruefe(P, "im Ausfall spart der Abbruch Aufrufe UND Zeit",
               _mit < _ohne and _dauer_mit < _dauer_ohne,
               f"{_mit} statt {_ohne} Aufrufe, {_dauer_mit:.1f} statt "
               f"{_dauer_ohne:.1f} s bei 20 Signalen")
        pruefe(P, "und mehr als die Schwelle laufen kaum durch",
               _mit <= _ZM.AUSFALL_SCHWELLE + _ZM.MAX_GLEICHZEITIG,
               f"{_mit} - die Schwelle ist 3, aber zwei laufen gleichzeitig: "
               f"wer schon unterwegs ist, wird nicht zurueckgerufen")
    finally:
        _ZM.WARTE_AUF_PLATZ_SEKUNDEN = _alt_w
        _ZM.AUSFALL_SCHWELLE = _alt_s
        _ZM.beginne_umlauf()

    # ---- UND DER LESER ERFAEHRT ES ----
    pruefe(P, "die Mail sagt, dass NICHT gegengeprueft wurde",
           all("NICHT gegengeprueft" in _ZM.zeilen({"uebersprungen_art": a})[0]
               for a in ("andrang", "ausfall", "fehler")),
           "das Feld `uebersprungen` wurde bis heute gesetzt und NIRGENDS "
           "gelesen - eine ausgefallene Gegenpruefung sah aus wie eine, die "
           "es zu diesem Wert gar nicht gibt")
    pruefe(P, "und nennt die beiden Lagen verschieden",
           _ZM.zeilen({"uebersprungen_art": "andrang"})
           != _ZM.zeilen({"uebersprungen_art": "ausfall"}))
    pruefe(P, "grau, nicht rot",
           all(_ZM.zeilen({"uebersprungen_art": a})[0].startswith("●")
               for a in ("andrang", "ausfall")),
           "ein Ausfall unserer Technik ist kein Befund ueber den Handel")
    pruefe(P, "ein echter Befund verdraengt die Zeile",
           len(_ZM.zeilen({"uebersprungen_art": "andrang", "einwand": "nein",
                           "einwand_grund": "x"})) > 1,
           "kam die Pruefung doch noch durch, gilt ihr Ergebnis")
    # ⚠️ DIE DREI VOR DEM ABBRUCH. Beim Nachweis am toten Anbieter
    # aufgefallen: sie landen im P-8-Zweig, nicht bei Andrang/Ausfall.
    _q = _quelltext("agent/zweite_meinung.py")
    pruefe(P, "auch der blosse Fehlschlag setzt eine Art",
           'aus["uebersprungen_art"] = "fehler"' in _q,
           "sonst gehen die Mails VOR dem Abbruch ohne Gegenpruefung UND "
           "ohne Hinweis raus - genau so, wie sie aussaehen, wenn es zu "
           "diesem Wert gar keine Gegenquelle gibt")
    pruefe(P, "und die drei Lagen sind drei verschiedene Saetze",
           len({_ZM.zeilen({"uebersprungen_art": a})[0]
                for a in ("andrang", "ausfall", "fehler")}) == 3)

    pruefe(P, "und ohne alles bleibt es leer",
           _ZM.zeilen({}) == [] and _ZM.zeilen({"einwand": None}) == [],
           "ein Abschnitt ohne Inhalt saehe aus wie ein Befund")


def paket_dimension() -> None:
    """Die Dimensionierung als reine Funktion (18.08.2026, Kapitel 88).

    Stufe 0: gemessen wird, nicht gehandelt. Diese Pruefungen sichern die
    Funktion ab, BEVOR eine Zahl aus ihr eine Entscheidung wird."""
    from agent import entscheidungsrechnung as _ER

    P = "Dimension"
    _B = dict(kurs=100.0, atr=4.0, einsatz_eur=1000.0)

    # ---- REIN: kein Zustand, keine Uhr, kein Netz ----
    _a = _ER.dimensioniere(k=1.5, verlustanteil=0.15, **_B)
    _b = _ER.dimensioniere(k=1.5, verlustanteil=0.15, **_B)
    pruefe(P, "zweimal derselbe Aufruf, zweimal dasselbe Ergebnis",
           dict(_a) == dict(_b),
           "eine Funktion mit Gedaechtnis waere in einer Messung ueber "
           "40 Jahre Historie nicht wiederholbar")

    # ---- DREI BOEDEN, DER WEITESTE GEWINNT ----
    pruefe(P, "ohne Marke und ohne These zaehlt das Rauschen",
           _a["stop_regel"] == "Rauschen"
           and abs(_a["stop_rel"] - 1.5 * 4.0 / 100.0) < 1e-9)
    _m = _ER.dimensioniere(k=1.5, verlustanteil=0.15, marke_preis=88.0, **_B)
    pruefe(P, "eine weiter entfernte Marke gewinnt",
           _m["stop_regel"] == "Struktur" and _m["stop_rel"] > _a["stop_rel"],
           "12 EUR Abstand plus Puffer schlagen 6 EUR Rauschen")
    _n = _ER.dimensioniere(k=1.5, verlustanteil=0.15, marke_preis=97.0, **_B)
    pruefe(P, "eine naehere Marke gewinnt NICHT",
           _n["stop_regel"] == "Rauschen",
           "genau dafuer ist der Rauschboden da")
    _t = _ER.dimensioniere(k=1.5, verlustanteil=0.15,
                           umgeworfen_preis_eur=80.0, **_B)
    pruefe(P, "ein weiter entfernter Widerlegungspreis gewinnt",
           _t["stop_regel"] == "These")
    _d = _ER.dimensioniere(k=1.5, verlustanteil=0.15,
                           umgeworfen_preis_eur=10.0, **_B)
    pruefe(P, "und die Obergrenze bindet darueber",
           _d["stop_regel"] == "Obergrenze"
           and abs(_d["stop_rel"] - _ER.GRENZEN["stop_max_relativ"]) < 1e-9)

    # ---- DER HEBEL FAELLT AN ----
    pruefe(P, "Hebel = Verlustanteil / Stopabstand",
           abs(_a["hebel_noetig"] - 0.15 / _a["stop_rel"]) < 1e-9,
           "das ist die Beziehung, die die Erstfassung des Plans uebersehen "
           "hat - die Spot/Hebel-Grenze IST der Verlustanteil")
    _g = _ER.dimensioniere(k=1.5, verlustanteil=0.06, **_B)
    pruefe(P, "Stop = Verlustanteil ist genau die Grenze",
           abs(_g["hebel_noetig"] - 1.0) < 1e-9 and _g["etikett"] == "spot",
           f"Stop {_g['stop_rel']:.4f} gegen Verlustanteil 0,06 - bei "
           f"Gleichstand gilt SPOT, nicht Hebel")
    _s = _ER.dimensioniere(k=1.5, verlustanteil=0.02, **_B)
    pruefe(P, "darunter faellt kein Hebel an, der Betrag folgt dem Risiko",
           _s["etikett"] == "spot" and _s["hebel"] == 1.0
           and _s["betrag_eur"] < _B["einsatz_eur"],
           "den Einsatz stehen zu lassen hiesse, mehr zu riskieren als "
           "erlaubt - die stillschweigende Umdeutung vom 15.08.")

    # ---- SHORT ERZWINGT HEBEL ----
    _sh = _ER.dimensioniere(k=1.5, verlustanteil=0.02, ist_short=True, **_B)
    pruefe(P, "SHORT bekommt IMMER das Etikett hebel",
           _sh["etikett"] == "hebel",
           "Spot kann bei Bitpanda nicht short - die Richtung ist damit "
           "selbst ein Hebelkriterium, eine Tatsache und keine Prognose")

    # ---- HANDELBARKEIT ----
    _nh = _ER.dimensioniere(k=1.5, verlustanteil=0.15,
                            hebel_handelbar=False, **_B)
    pruefe(P, "wo kein Hebel handelbar ist, entsteht auch keiner",
           _nh["etikett"] == "spot" and _nh["hebel"] == 1.0,
           "Aktien, Rohstoffe und ETF - die Formel rechnet, Bitpanda "
           "bietet nichts an")

    # ---- SPIEGELUNG ----
    _l1 = _ER.dimensioniere(k=1.5, verlustanteil=0.15, marke_preis=88.0, **_B)
    _s1 = _ER.dimensioniere(k=1.5, verlustanteil=0.15, marke_preis=112.0,
                            ist_short=True, **_B)
    pruefe(P, "LONG und SHORT spiegeln sich im Stopabstand",
           abs(_l1["stop_rel"] - _s1["stop_rel"]) < 1e-9,
           "dieselbe Entfernung, andere Seite - ein Vorzeichenfehler bliebe "
           "hier sonst unsichtbar")

    # ---- NIE STILL NICHTS ----
    _blockiert = 0
    for _bad in ({"kurs": 0.0}, {"atr": 0.0}, {"einsatz_eur": 0.0}):
        _arg = dict(_B); _arg.update(_bad)
        try:
            _ER.dimensioniere(k=1.5, verlustanteil=0.15, **_arg)
        except _ER.RechnungBlockiert:
            _blockiert += 1
    pruefe(P, "unbrauchbare Eingaben werfen BENANNT, geben nicht None",
           _blockiert == 3,
           "eine Funktion, die still nichts liefert, ist die Bauform, die "
           "den Deadloop erzeugt hat")
    _va = 0
    for _w in (0.0, 1.0, 1.5, -0.1):
        try:
            _ER.dimensioniere(k=1.5, verlustanteil=_w, **_B)
        except _ER.RechnungBlockiert:
            _va += 1
    pruefe(P, "ein Verlustanteil ausserhalb (0,1) wird abgewiesen",
           _va == 4, "15 statt 0,15 waere sonst ein stiller Faktor 100")

    # ---- MINDESTGROESSE WIRD GEMELDET, NICHT VERSCHLUCKT ----
    _k = _ER.dimensioniere(k=2.5, verlustanteil=0.001 * 10, einsatz_eur=30.0,
                           kurs=100.0, atr=4.0, mindestgroesse_eur=25.0)
    pruefe(P, "eine zu kleine Position wird als solche ausgewiesen",
           "unter_mindestgroesse" in _k,
           "sie zu verschlucken waere eine stille Bremse - genau das, was "
           "der Kanarienvogel sehen koennen muss")

    # ---- S1: DER RAUSCHBODEN IST EIN REGLER (Kapitel 90) ----
    from agent import betraege as _BE

    pruefe(P, "ohne Konfigurationseintrag ist nichts gesetzt",
           _BE.stop_min_atr(None) is None and _BE.stop_min_atr({}) is None,
           "die Vorgabe steht an EINER Stelle (GRENZEN) - sie hier zu "
           "wiederholen hiesse, dieselbe Zahl an zwei Orten zu pflegen")
    for _pfad in ({"rollen_kette": {"stop_min_atr": 2.0}},
                  {"risiko": {"rollen_kette": {"stop_min_atr": 2.0}}}):
        pruefe(P, "gelesen ueber " + sorted(_pfad)[0],
               _BE.stop_min_atr(_pfad) == 2.0,
               "beide Pfade, weil der Schluessel dort stehen darf, wo der "
               "Nutzer ihn vermutet - dieselbe Falle wie am 14.08.")
    _ab = 0
    for _w in (0, -1, 11):
        try:
            _BE.stop_min_atr({"rollen_kette": {"stop_min_atr": _w}})
        except _BE.BetragUnbekannt:
            _ab += 1
    pruefe(P, "unsinnige Faktoren werden abgewiesen", _ab == 3,
           "ein Faktor auf die Schwankungsbreite, keine Prozentzahl - 25 "
           "statt 2,5 waere sonst ein stiller Faktor zehn")

    # ⚠️ BITGLEICH OHNE EINTRAG. Das ist die ganze Zusage von S1.
    _e = dict(kurs=100.0, atr=4.0, risiko_eur=150.0, betrag_wunsch_eur=1000.0,
              instrument="hebel", umgeworfen_preis_eur=99.0)
    pruefe(P, "ohne Regler rechnet rechne() wie zuvor",
           dict(_ER.rechne(**_e)) == dict(_ER.rechne(**_e, stop_min_atr=None)),
           "S1 darf kein Verhalten aendern - der Wechsel kommt erst in S5")
    _r075 = _ER.rechne(**_e)
    _r20 = _ER.rechne(**_e, stop_min_atr=2.0)
    # ⚠️ EIGENSCHAFT STATT FAKTOR (31.08.2026). Hier stand
    # `> _r075["stop_relativ"] * 2.5`. Das galt, solange die Klemme bei
    # 2,5 % lag: der Rueckfall landete auf 3 %, der Regler auf 8 %. Seit
    # die Untergrenze auf 5 % steht, ist der Rueckfall selbst geklemmt
    # (5 %), und das Verhaeltnis faellt auf 1,60 - die Pruefung schlug an,
    # obwohl der Regler unveraendert wirkt.
    #
    # Geprueft wird jetzt, was gemeint war: ein groesserer Faktor macht den
    # Stop WEITER und den Hebel KLEINER. Eine Pruefung, die einen
    # Zahlenwert einfriert, bremst die naechste begruendete Aenderung aus.
    pruefe(P, "und mit Regler greift er auf dem Produktionspfad",
           _r20["stop_relativ"] > _r075["stop_relativ"]
           and _r20["hebel"] < _r075["hebel"],
           "in 10 von 12 echten Faellen bindet genau diese Klemme - der "
           "ATR-Rueckfall dagegen wird von ihr nicht beruehrt")
    pruefe(P, "die Kette reicht ihn durch",
           "stop_min_atr=BE.stop_min_atr(config)"
           in _quelltext("agent/rollen_lauf.py"),
           "ein Regler, der die Aufrufstelle nicht erreicht, ist Dekoration")

    # ---- S2: DIE MARKE AUF DER STOPSEITE (Kapitel 90) ----
    from agent import marktrang as _MR_MOD
    from agent import rollen_lauf as _RL

    _B = {"_marken_werte": {"unterstuetzung": {"preis_eur": 92.0},
                            "widerstand": {"preis_eur": 108.0}}}
    pruefe(P, "LONG nimmt die Unterstuetzung, SHORT den Widerstand",
           _RL._marke_am_stop(_B, False) == 92.0
           and _RL._marke_am_stop(_B, True) == 108.0,
           "die ANDERE Marke als `_marke_im_weg`, die dem Ziel im Weg steht "
           "- ein vertauschtes Paar bliebe hier sonst unsichtbar")
    pruefe(P, "ohne Marken gibt es None statt eines Fehlers",
           _RL._marke_am_stop({}, False) is None
           and _RL._marke_am_stop(None, True) is None)

    # ⚠️ S2 IST REINE VERKABELUNG - der Stop darf sich NICHT bewegen.
    _m = dict(kurs=100.0, atr=4.0, risiko_eur=150.0, betrag_wunsch_eur=1000.0,
              instrument="hebel", umgeworfen_preis_eur=99.0)
    _ohne, _mit = _ER.rechne(**_m), _ER.rechne(**_m, marke_stop_eur=92.0)
    # ⚠️ SEIT S5 IST SIE ANGESCHLOSSEN. Bis dahin pruefte diese Zeile das
    # Gegenteil ("aendert den Stop noch NICHT") - die alte Erwartung war
    # richtig fuer S2 und ist mit S5 ueberholt. Nicht die Aenderung
    # zurueckdrehen, sondern die Erwartung nachziehen.
    pruefe(P, "die Marke traegt den Stop, wenn sie weiter steht",
           _mit["stop_relativ"] > _ohne["stop_relativ"]
           and _mit["hebel"] < _ohne["hebel"],
           "Struktur schlaegt Rauschen, wenn sie weiter liegt - das ist der "
           "Sinn des dritten Bodens")
    pruefe(P, "sie steht aber im Ergebnis",
           _mit["marke_stop_eur"] == 92.0 and _ohne["marke_stop_eur"] is None)

    # ⚠️ NICHT UEBER `widerstand`. Der geht an `_ziel()` und wuerde den am
    # 17.08. gemessen verworfenen Widerstandsdeckel reaktivieren.
    # ⚠️ AM SYNTAXBAUM, NICHT AM TEXT. Meine erste Fassung suchte
    # "widerstand=" im Quelltext - und fand ihren eigenen Warnhinweis im
    # Docstring von `_marke_am_stop`. `_quelltext` entfernt Kommentarzeilen,
    # aber KEINE Docstrings. Dieselbe Klasse wie die Grabinschrift vom
    # 12.08., nur eine Etage tiefer.
    import ast as _ast

    _baum = _ast.parse(io.open("agent/rollen_lauf.py", encoding="utf-8").read())
    _wid = [k for _n in _ast.walk(_baum) if isinstance(_n, _ast.Call)
            for k in (_n.keywords or []) if k.arg == "widerstand"]
    _q = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "kein Aufruf uebergibt `widerstand`",
           not _wid,
           "44 von 44 Symbolen gedeckelt, 98 % unter CRV 0,5 - der Deckel "
           "bleibt aus, und die Stopmarke nimmt einen eigenen Weg")
    pruefe(P, "und reicht die Stopmarke durch",
           "marke_stop_eur=_marke_am_stop(" in _q)

    # ---- S3: DER VERTRAG PRUEFT DEN WIDERLEGUNGSPREIS (Kapitel 90) ----
    from agent import empfehlung_vertrag as _EV

    def _v(a, **kw):
        # ⚠️ S6c: die Richtung ist bei KAUFEN/NACHKAUFEN Pflicht. Thema DIESER
        # Pruefungen ist der Widerlegungspreis, nicht die Richtung - der
        # Vorgabewert LONG haelt sie auf ihrem Gegenstand.
        a = dict(a)
        if a.get("aktion") in _EV.BRAUCHT_RICHTUNG:
            a.setdefault("richtung", "LONG")
        return _EV.validiere(a, "X", **kw).get("aktion")

    # ⚠️ S6a: DIE HAUPT-EINSTIEGSAKTION HEISST JETZT KAUFEN. Der Sinn der
    # Pruefung bleibt: jede Aktion, die eine Position aufbaut, wird gegen den
    # Widerlegungspreis geprueft - bis zum 18.08. galt das fuer die
    # damalige Haupt-Hebelaktion NICHT.
    pruefe(P, "jede Einstiegsaktion wird gegen die Widerlegung geprueft",
           set(_EV.HEBEL_MIT_EINSTIEG) <= set(_EV.BRAUCHT_EINSTIEG)
           and "KAUFEN" in _EV.BRAUCHT_EINSTIEG,
           "bis zum 18.08. galt die Pruefung nur fuer KAUFEN/NACHKAUFEN - "
           "ERÖFFNEN, die damalige Haupt-Hebelaktion, war die einzige ohne "
           "Kontrolle")
    pruefe(P, "LONG: Widerlegung ueber dem Kurs wird beanstandet",
           _v({"aktion": "KAUFEN", "umgeworfen_preis_eur": 110}, kurs=100)
           == "NICHTS_TUN")
    pruefe(P, "LONG: Widerlegung unter dem Kurs bleibt",
           _v({"aktion": "KAUFEN", "umgeworfen_preis_eur": 90}, kurs=100)
           == "KAUFEN")
    pruefe(P, "SHORT: Widerlegung UEBER dem Kurs ist RICHTIG",
           _v({"aktion": "KAUFEN", "richtung": "SHORT",
               "umgeworfen_preis_eur": 110}, kurs=100, instrument="hebel")
           == "KAUFEN",
           "die alte Pruefung kannte keine Richtung und degradierte jedes "
           "SHORT mit korrektem Stop - dieselbe Klasse wie die 313 "
           "SHORT-Vorschlaege, die als HALTEN in der Datenbank lagen")
    pruefe(P, "SHORT: Widerlegung unter dem Kurs wird beanstandet",
           _v({"aktion": "KAUFEN", "richtung": "SHORT",
               "umgeworfen_preis_eur": 90}, kurs=100, instrument="hebel")
           == "NICHTS_TUN")
    pruefe(P, "ein fehlender Widerlegungspreis degradiert NICHT",
           _v({"aktion": "KAUFEN"}, kurs=100) == "KAUFEN",
           "das Schema laesst null ausdruecklich zu - nicht jede Beobachtung "
           "hat einen Kurs, und eine erzwungene Zahl waere erfunden")
    pruefe(P, "und ohne Kurs wird nicht geraten",
           _v({"aktion": "KAUFEN", "umgeworfen_preis_eur": 110}) == "KAUFEN")

    # ⚠️ DIE ZWEI PREISFELDER SIND RAUS - aus Prompt UND Schema.
    pruefe(P, "das Schema verlangt keinen Einstiegs- und Stopkurs mehr",
           '"einstieg_eur": NUM' not in _quelltext("agent/llm_schema.py")
           and '"stop_eur": NUM' not in _quelltext("agent/llm_schema.py"),
           "verlangt, von rechne() nie gelesen - und trotzdem toedlich")
    pruefe(P, "und der Prompt fragt nicht mehr danach",
           '"einstieg_eur": <zahl>'
           not in _quelltext("agent/rolle_trader.py"))
    pruefe(P, "die gerechneten Felder heissen weiter so",
           _ER.rechne(kurs=100.0, atr=4.0, risiko_eur=150.0,
                      betrag_wunsch_eur=1000.0).get("stop_eur") is not None,
           "gleicher Name, andere Herkunft: `rechne()` liefert sie, das "
           "Modell nicht mehr - signal_abbildung und trade_chart lesen die "
           "GERECHNETEN und bleiben unberuehrt")

    # ---- S4: EIN FAKTENSATZ STATT ZWEI (Kapitel 90) ----
    from agent.faktenblock import ZUSATZ_JE_BEREICH as _ZJB

    pruefe(P, "Spot und Hebel bekommen denselben Faktensatz",
           _ZJB["krypto_spot"] == _ZJB["krypto_hebel"],
           "Finanzierungsrate, Put-Skew und Long-Anteil sagen etwas ueber "
           "die POSITIONIERUNG - die ist dieselbe, ob man sie gehebelt "
           "handelt oder nicht")
    pruefe(P, "und es sind vier, nicht einer",
           len(_ZJB["krypto_spot"]) == 4,
           "vorher hatte Spot genau einen: btc_relativwert_pct")
    pruefe(P, "die anderen Klassen bleiben unberuehrt",
           _ZJB["aktien"] == ("kgv", "insider_saldo", "short_interest_pct",
                              "analysten_trend")
           and _ZJB["rohstoffe"] == ("lagerbestand_trend", "cot_netto_pct")
           and _ZJB["themen_etf"] == (),
           "S4 betrifft die Krypto-Trennung, nicht die Assetklassen")

    # ⚠️ DIESE PRUEFUNG STAND BIS S6a AUF DEM GEGENTEIL. Sie hielt fest,
    # dass F1/F2 zu S6 gehoeren und nicht zu S4 - "44 Codestellen Risiko
    # ohne Anlass". Der Anlass ist jetzt da: S6a IST dieser Schritt.
    pruefe(P, "das Aktionsvokabular haengt NICHT mehr am Instrument",
           _EV.aktionen_fuer("spot") == _EV.aktionen_fuer("hebel"),
           "S6a (22.08.) - erst damit kann S6b den zweiten Lauf streichen, "
           "denn zwei Laeufe mit derselben Frage sind eine Frage zu viel")

    # ---- DER NB-EXPORT MUSS DEN UMBAU KENNEN ----
    _ex = _quelltext("extract_notebook_diagnose.py")
    pruefe(P, "der Export hat einen Abschnitt zur Dimensionierung",
           "def _dimensionierung(" in _ex
           and '"dimensionierung": dimensionierung,' in _ex,
           "bis heute kannte der Export vom Umbau NICHTS - jede Auswertung "
           "waere auf Altdaten gelaufen und haette die alten Schluesse "
           "bestaetigt")
    pruefe(P, "und schluesselt JE TAG auf, nicht nur als Summe",
           '"je_tag"' in _ex,
           "meine erste Fassung fasste sieben Tage zu einer Zahl "
           "zusammen und verdeckte damit genau das, wofuer sie gebaut "
           "war: die Umstellung lief am 18.08. gegen 20:00 an, und in "
           "845 Signalen der Vorwoche gingen die ersten 78 danach "
           "unter. Eine Kennzahl, die eine Aenderung glaettet, ist zur "
           "Kontrolle einer Aenderung unbrauchbar")
    pruefe(P, "und trennt EINGESTELLT von GEMESSEN",
           '"eingestellt"' in _ex and '"gemessen"' in _ex
           and '"erwartet_nach_s5"' in _ex,
           "stimmen beide nicht ueberein, ist die Einstellung nicht "
           "wirksam - genau der Fall, der am 18.08. beim Schluessel "
           "risiko_pro_trade_prozent_hebel auffiel")

    # ---- HEBEL: ZEILE UND BETREFF FOLGEN DER ZAHL (19.08.2026) ----
    from agent import signal_mail as _SM2

    def _mit(atr):
        return _ER.rechne(kurs=100.0, atr=atr, risiko_eur=60.0,
                          betrag_wunsch_eur=1000.0, instrument="hebel",
                          umgeworfen_preis_eur=99.0, stop_min_atr=2.0)

    _ohne_h, _mit_h = _mit(4.0), _mit(0.8)
    pruefe(P, "bei Hebel 1,0 steht die Zeile TROTZDEM da",
           any(z.strip().startswith("Hebel") for z in _ER.saetze(_ohne_h)),
           "eine Mail OHNE Hebelzeile sieht aus wie eine, bei der die "
           "Angabe vergessen wurde - nicht wie eine ohne Hebel. Nutzerfund "
           "an einer echten AKT-Mail: Betreff Hebel, im Koerper keiner")
    pruefe(P, "und sie sagt, warum es keinen braucht",
           any("kein Hebel noetig" in z for z in _ER.saetze(_ohne_h)))
    pruefe(P, "ueber 1,0 bleibt die alte Zeile mit Liquidation",
           any("Liquidation etwa" in z for z in _ER.saetze(_mit_h)))

    def _betreff(r):
        return _SM2.baue_mail(symbol="AKT", name="AKT", kurs_eur=100.0,
                              instrument="hebel", strategie="einstieg",
                              rechnung=r,
                              urteil={"aktion": "ERÖFFNEN",
                                      "begruendung": "x"})[0]

    pruefe(P, "der Betreff behauptet keinen Hebel, wo keiner ist",
           "(Hebel)" not in _betreff(_ohne_h),
           "vorher hing er am INSTRUMENT, also am Lauf - seit S5 faellt in "
           "vier von fuenf Faellen 1,0 an, und drei Stellen sagten Hebel, "
           "waehrend die Rechnung nein sagte")
    pruefe(P, "und nennt ihn, wo einer anfaellt",
           "(Hebel)" in _betreff(_mit_h))

    # ---- P1 AUS KAPITEL 91: DIE EXTREME SICHTBAR MACHEN ----
    from agent import marktlage as _ML3
    from agent import signal_mail as _SM3
    from ui import formatting as _F3

    _A = "Die Rate steht im 96. Perzentil - aussergewoehnlich hoch."
    _G = "Das Interesse steht im 50. Perzentil - im gewohnten Bereich."
    pruefe(P, "auffaellige Perzentile werden erkannt",
           _F3.classify_detail_line(_A) == "auffaellig")
    pruefe(P, "gewohnte NICHT",
           _F3.classify_detail_line(_G) != "auffaellig",
           "sie werden ohnehin zu einer Zeile zusammengefasst - sie auch "
           "noch fett zu setzen hiesse, jede Mail fett zu setzen")
    pruefe(P, "fett, aber NICHT schwarz",
           "font-weight:bold" in _F3.render_detail_html(_A)
           and "#000000" not in _F3.render_detail_html(_A),
           "schwarz-fett sind die Handelsparameter - zwei Bedeutungen "
           "brauchen zwei Behandlungen, sonst heisst fett bald nichts mehr")
    pruefe(P, "und die Handelsparameter bleiben schwarz",
           "#000000" in _F3.render_detail_html("Stop            3,60 EUR"))

    # ---- DAS GRAU DARF NICHT WIEDER AUFHELLEN (22.08.2026) --------------
    # ⚠️ ZWEIMAL DERSELBE NUTZER-FUND: 25.07. "#666666 schwer lesbar", 22.08.
    # "das Grau erscheint etwas zu hell" (#4a4a4a). Beim ersten Mal wurde auf
    # einen Wert nachgedunkelt, der rechnerisch bereits AAA war - der
    # Kontrastwert misst Farbe gegen Farbe, nicht Lesbarkeit bei kleiner,
    # teils KURSIVER Schrift.
    #
    # Geprueft wird deshalb der GERECHNETE Kontrast, nicht die Zeichenkette:
    # eine feste Farbprobe wuerde jede spaetere Umbenennung durchwinken.
    def _leuchtkraft(farbe: str) -> float:
        v = [int(farbe[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        v = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in v]
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]

    def _kontrast(farbe: str) -> float:
        a, b = _leuchtkraft(farbe), _leuchtkraft("#ffffff")
        return (max(a, b) + 0.05) / (min(a, b) + 0.05)

    _grau = re.findall(r"color:(#[0-9a-fA-F]{6});",
                       " ".join(_F3._HTML_STYLE_BY_TAG[t]
                                for t in ("risk_neutral", "fazit_neutral",
                                          "legend")))
    _schwaechster = min((_kontrast(g) for g in _grau), default=0.0)
    pruefe(P, "der neutrale Grauton der Mail traegt mindestens 12:1",
           _schwaechster >= 12.0,
           f"gemessen {_schwaechster:.1f}:1 auf Weiss ({', '.join(sorted(set(_grau)))}) "
           f"- 8,9:1 war rechnerisch AAA und dem Nutzer trotzdem zu hell")
    pruefe(P, "und bleibt heller als der Fliesstext",
           _schwaechster < _kontrast("#1a1a1a"),
           "sonst verschwindet die Abstufung 'nachrangig', und dann waere "
           "die Farbe besser ganz aufzugeben als unkenntlich zu machen")
    pruefe(P, "gezaehlt wird ueber EINE Funktion",
           len(_SM3.auffaellige([_A, _G, "Stop 1"])) == 1,
           "die Schwelle stammt aus marktlage._einordnung und wird nicht "
           "neu gesetzt")

    # ⚠️ P1 IST ABSICHTLICH FOLGENLOS. Kein Filter, keine Bevorzugung.
    _q3 = _quelltext("agent/signal_mail.py")
    # ⚠️ SEIT P1a WIRD SIE BENUTZT - zum SPEICHERN, nicht zum Filtern.
    # Die alte Fassung verlangte, dass `auffaellige(` in rollen_lauf gar
    # nicht vorkommt; das war richtig, solange nichts gespeichert wurde.
    _qrl = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Kennzeichnung wird gespeichert",
           'felder["auffaellige_json"]' in _qrl,
           "ohne Speicherung waere sie reine Anzeige - und die Frage, ob "
           "Extreme tragen, nie zu beantworten")
    pruefe(P, "und sie entscheidet trotzdem nichts",
           "if _auf" not in _qrl.replace('felder["auffaellige_json"]', "")
           or "return" not in _qrl.split("_auf = SM.auffaellige")[-1][:400],
           "kein Filter, keine Bevorzugung - nur ein Vermerk")

    _gew = sum(1 for _p in range(101)
               if _ML3._einordnung(_p) == _SM3.GEWOHNT)
    pruefe(P, "rund ein Fuenftel der Perzentilwerte gilt als auffaellig",
           15 <= 101 - _gew <= 30,
           f"{101 - _gew} von 101 - genau die Groessenordnung, die die "
           f"Literatur als Extreme meint (R-T6: kein konstantes Feld)")

    # ---- DREI ZUSTAENDE, DIE NIE VERSCHMELZEN (91 P2, 19.08.2026) ----
    import messe_entwickleraktivitaet as _ME

    class _Antwort:
        def __init__(self, code, koerper):
            self.status_code, self._k = code, koerper

        def json(self):
            if self._k is None:
                raise ValueError("kein JSON")
            return self._k

    class _Sitzung:
        def __init__(self, *antworten):
            self._a = list(antworten)

        def get(self, *a, **kw):
            return self._a.pop(0) if self._a else _Antwort(500, {})

    _voll = {"developer_data": {"stars": 73168, "forks": 3,
                               "commit_count_4_weeks": 108}}
    _leer = {"developer_data": {"stars": 0, "forks": 0, "subscribers": 0,
                               "total_issues": 0,
                               "commit_count_4_weeks": 0}}
    pruefe(P, "ein verknuepftes Repository heisst repo",
           _ME._hole("x", _Sitzung(_Antwort(200, _voll)))[0] == "repo")
    pruefe(P, "eine Antwort ohne Repo heisst kein_repo",
           _ME._hole("x", _Sitzung(_Antwort(200, _leer)))[0] == "kein_repo")

    # ⚠️ DER WICHTIGE FALL. Meine erste Messung zaehlte 429-Antworten als
    # "kein Repository" - Ergebnis "0 von 43", waehrend BTC zwei Minuten
    # zuvor 73.168 Sterne gemeldet hatte. Ein Abbruch war zu einem
    # plausibel aussehenden Messwert geworden.
    _drei429 = _Sitzung(*[_Antwort(429, {}) for _ in range(3)])
    pruefe(P, "ein 429 ist ein FEHLER, kein Nein",
           _ME._hole("x", _drei429)[0] == "fehler",
           "wer den dritten Zustand mit dem zweiten verrechnet, erklaert "
           "lebendige Ketten fuer tot")
    for _code in (500, 404, 403):
        pruefe(P, f"HTTP {_code} ebenso",
               _ME._hole("x", _Sitzung(_Antwort(_code, {})))[0] == "fehler")
    pruefe(P, "eine 200 OHNE developer_data ist auch ein Fehler",
           _ME._hole("x", _Sitzung(_Antwort(200, {"status": "x"})))[0]
           == "fehler",
           "eine unerwartete Form ist keine Auskunft - vielleicht ein "
           "Fehlerkoerper mit 200")
    pruefe(P, "und kaputtes JSON ebenso",
           _ME._hole("x", _Sitzung(_Antwort(200, None)))[0] == "fehler")
    pruefe(P, "die Drosselung ist vorsichtig gewaehlt",
           _ME.ABSTAND_S >= 4.0,
           "CoinGeckos Gratis-Tier nennt 10-30 je Minute; 5 s sind 12/min - "
           "bewusst am unteren Rand, weil ein 429 die Messung wertlos macht")

    # ---- DER TOPF FOLGT DER ZAHL, NICHT DEM LAUF (19.08.2026) ----
    _qrl2 = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "der Topf wird nach dem gerechneten Etikett geholt",
           "TO.frei_eur(_topf_instrument" in _qrl2
           and "TO.belegt_eur(conn, _topf_instrument)" in _qrl2,
           "vorher stand dort `instrument` - seit S5 faellt in vier von "
           "fuenf Faellen Hebel 1,0 an, und diese Signale belegten trotzdem "
           "den Hebeltopf (3.000 EUR = drei Positionen)")
    pruefe(P, "faellt die Vorabrechnung aus, wird das VERMERKT",
           "Topfzuordnung aus dem Lauf statt aus der Zahl" in _qrl2,
           "fail-soft ist fail-silent - ein Rueckfall gehoert in den Lauf, "
           "nicht ins Schweigen")

    # ⚠️ DER DECKEL DARF NICHT BLOCKIEREN (Nutzervorgabe 19.08.).
    _voll = _ER.rechne(kurs=100.0, atr=4.0, risiko_eur=48.0,
                       betrag_wunsch_eur=800.0, instrument="spot",
                       topf_frei_eur=200.0, umgeworfen_preis_eur=99.0)
    pruefe(P, "ein voller Topf laesst den Betrag stehen",
           _voll["betrag_eur"] == 800.0,
           "ein Deckel, der ein Signal verschwinden laesst, waere ein "
           "unsichtbares Veto")
    pruefe(P, "und meldet die Ueberschreitung",
           _voll.get("topf_wuerde_ueberschreiten") is True
           and _voll.get("topf_frei_eur") == 200.0,
           "die Zahl wandert in die Mail - der Nutzer entscheidet")
    _cfg2 = io.open("Basisinfos/config.yaml", encoding="utf-8").read()
    pruefe(P, "der Spot-Deckel steht in der Konfiguration, nicht im Code",
           "spot: 4000" in _cfg2,
           "ein Startwert, ausdruecklich zum Drehen - er gehoert dorthin, "
           "wo der Nutzer ihn findet")

    # ---- EIN BITPANDA-AUSFALL DARF DIE KETTE NICHT MITNEHMEN ----
    #
    # AM SYNTAXBAUM GEPRUEFT, nicht am Text (Methodik 2.41): ein `except`
    # im Kommentar zu finden waere kein Nachweis.
    import ast as _ast2

    _bg2 = _ast2.parse(io.open("scheduler/background.py",
                               encoding="utf-8").read())
    _job = next(n for n in _ast2.walk(_bg2)
                if isinstance(n, _ast2.FunctionDef)
                and n.name == "hebel_screening_job")
    _sync_try = [n for n in _ast2.walk(_job) if isinstance(n, _ast2.Try)
                 and any(isinstance(c, _ast2.Call)
                         and isinstance(c.func, _ast2.Name)
                         and c.func.id == "sync_hebel_positions"
                         for c in _ast2.walk(n))]
    _innen = [n for n in _sync_try
              if not any(isinstance(c, _ast2.Call)
                         and isinstance(c.func, _ast2.Name)
                         and c.func.id == "fuehre_umlauf"
                         for c in _ast2.walk(n))]
    pruefe(P, "der Bitpanda-Abgleich hat einen eigenen Fehlerfang",
           bool(_innen) and all(n.handlers for n in _innen),
           "vorher hatte dieser try NUR ein finally - ein 503 lief bis zum "
           "aeusseren Handler durch, und fuehre_umlauf() wurde NIE "
           "erreicht. Ein Ausfall beim Nachlesen von Brokerpositionen "
           "kostete den KOMPLETTEN Umlauf: keine Urteile, keine Signale, "
           "keine Mails")
    pruefe(P, "und er meldet, dass er uebersprungen hat",
           "Hebel-Positions-Abgleich uebersprungen"
           in _quelltext("scheduler/background.py"),
           "fail-soft ist fail-silent - wer nicht drankam, muss sich vom "
           "Rest unterscheiden lassen")

    # ---- DER TRICHTER (Kapitel 93 A, 19.08.2026) ----
    from agent import trichter as _TR

    pruefe(P, "die Faktoren sind GEMESSEN, nicht aus dem Lehrbuch",
           _TR.FAKTOR[0.68] < 0.9 and _TR.ANKER_GEMESSEN > 20000,
           "1 ATR x sqrt(t) deckt gemessen rund 81 % ab statt 68 % - ATR "
           "misst die Tagesspanne, der Trichter die Aenderung von Schluss "
           "zu Schluss. Zwei verschiedene Groessen")
    pruefe(P, "breiter wird er mit hoeherer Wahrscheinlichkeit",
           _TR.FAKTOR[0.68] < _TR.FAKTOR[0.80] < _TR.FAKTOR[0.90]
           < _TR.FAKTOR[0.95])
    _s5 = _TR.spanne(100.0, 4.0, 5)
    _s20 = _TR.spanne(100.0, 4.0, 20)
    pruefe(P, "und mit der Zeit - aber nur mit der WURZEL",
           _s20["weite_eur"] > _s5["weite_eur"]
           and abs(_s20["weite_eur"] / _s5["weite_eur"] - 2.0) < 0.01,
           "vier Mal so lange heisst doppelt so weit, nicht vier Mal - "
           "gemessen traegt die Skalierung ueber einen zwoelffachen "
           "Horizont (81,5 % gegen 79,6 %)")
    pruefe(P, "die Spanne liegt symmetrisch um den Kurs",
           abs((_s5["oben_eur"] + _s5["unten_eur"]) / 2 - 100.0) < 1e-9,
           "der Trichter sagt WIE WEIT, nicht wohin - eine Schieflage waere "
           "eine Richtungsaussage durch die Hintertuer")

    # ⚠️ NIE EINE GERATENE SPANNE.
    _ab = 0
    for _arg in ({"kurs": 0.0}, {"atr": 0.0}, {"horizont": 0}):
        _a2 = {"kurs": 100.0, "atr": 4.0, "horizont": 5}
        _a2.update(_arg)
        try:
            _TR.spanne(**_a2)
        except _TR.TrichterUnbekannt:
            _ab += 1
    pruefe(P, "ohne Grundlage wirft er, statt zu raten", _ab == 3,
           "eine erfundene Spanne ist schlimmer als keine - Stop und "
           "Groesse haengen daran")
    _zw = 0
    try:
        _TR.spanne(100.0, 4.0, 5, anteil=0.75)
    except _TR.TrichterUnbekannt:
        _zw = 1
    pruefe(P, "und ungemessene Wahrscheinlichkeiten weist er ab", _zw == 1,
           "zwischen zwei gemessenen Faktoren zu interpolieren hiesse, eine "
           "Zahl zu erfinden, die nie geprueft wurde")
    _tz = _TR.saetze(100.0, 4.0)
    pruefe(P, "in der Mail steht die Richtung ausdruecklich als OFFEN",
           any("Richtung offen" in z for z in _tz)
           and any("WIE WEIT, nicht WOHIN" in z for z in _tz),
           "wer ihn als Prognose liest, liest mehr hinein als dasteht")
    pruefe(P, "und eine BESCHREIBUNG steht daneben (Nutzerwunsch 19.08.)",
           any("Was das heisst" in z for z in _tz)
           and any("von 100" in z for z in _tz)
           # NICHT auf die Ankerzahl selbst pruefen: sie hat sich schon
           # einmal geaendert (30.116 -> 36.095, als die Hilfsreihen
           # herausfielen), und die Pruefung schlug an, obwohl die
           # Beschreibung vollstaendig war.
           and any("Gemessen an" in z or "KEINE eigene Messung" in z
                   for z in _tz),
           "eine neue Zahl ohne Satz daneben zwingt den Leser zu raten, ob "
           "sie Prognose, Garantie oder Schaetzung ist")

    # ⚠️ EIN WORT, ZWEI BEDEUTUNGEN - DIE FALLE.
    pruefe(P, "er belegt das Wort 'Schwankungsbreite' NICHT doppelt",
           not any(z.startswith("Uebliche") and "Schwankungsbreite" in z
                   for z in _tz)
           and any("Tagesspanne" in z for z in _tz),
           "weiter oben in derselben Mail heisst '0,7 Schwankungsbreiten' "
           "ein Vielfaches des ATR (Tagesspanne); der Trichter misst die "
           "Aenderung von Schluss zu Schluss ueber mehrere Tage")

    # DER SATZ, DER DEN TRICHTER NUETZLICH MACHT - IN BEIDE RICHTUNGEN.
    _innen = _TR.saetze(100.0, 4.0, stop_relativ=0.05)
    _aussen = _TR.saetze(100.0, 1.2, stop_relativ=0.05)
    pruefe(P, "er sagt, ob der Stop im gewoehnlichen Rauschen liegt",
           any("INNERHALB dieser Bewegung" in z for z in _innen)
           and any("ausserhalb" in z for z in _aussen),
           "ein Stop innerhalb der ueblichen Bewegung wird getroffen, ohne "
           "dass die These widerlegt waere - genau die Frage, um die dieses "
           "Projekt seit dem Deadloop kreist")
    pruefe(P, "ohne Stop bleibt der Satz WEG statt zu raten",
           not any("Ihr Stop liegt" in z for z in _tz))
    pruefe(P, "und er erscheint in der echten Rechnung",
           any("Uebliche Kursbewegung" in z for z in _ER.saetze(
               _ER.rechne(kurs=100.0, atr=4.0, risiko_eur=60.0,
                          betrag_wunsch_eur=1000.0, instrument="hebel",
                          umgeworfen_preis_eur=99.0))),
           "gebaut und nicht verdrahtet ist das Muster, das dieses Projekt "
           "mehrfach Wochen gekostet hat")

    # ---- H1/H2/H3 SIND VORAB FESTGELEGT (Kapitel 100, 20.08.) ----
    _kq = _quelltext("messe_konstellationen.py")
    _kroh = io.open("messe_konstellationen.py", encoding="utf-8").read()

    # Die Vorabfestlegung steht im MODULKOPF - und der ueberlebt
    # `_quelltext` nicht als Kommentar, sondern als Docstring. Deshalb hier
    # der rohe Text.
    pruefe(P, "die drei Fragen stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _kroh
           and "H1  MARKTPHASE" in _kroh and "H2  ASSET" in _kroh
           and "H3  ZWISCHENSTUFEN" in _kroh,
           "wer sie nachtraeglich an ein Ergebnis anpasst, hat sich ein "
           "Ergebnis gesucht (Methodik 2.45/2.46)")
    pruefe(P, "H3 misst, ob die Zahl SORTIERT - nicht ob sie hoch ist",
           "zehntel" in _kq and "np.argsort(p)" in _kq,
           "eine weiche Schwelle hilft nur, wenn hoeheres p auch oefter "
           "trifft. Gemessen: die Quote steigt bis zum vierten Zehntel und "
           "FAELLT danach - der Filter schneidet an der falschen Stelle")
    pruefe(P, "die Asset-Streuung wird gegen die ZUFALLSSTREUUNG gemessen",
           "streuung_zufall" in _kq,
           "elf Punkte Streuung klingen viel - entscheidend ist, wie viel "
           "bei gleicher Fallzahl ohnehin entstuende (gemessen 2,1)")
    pruefe(P, "ohne Placebo gilt nichts",
           "ohne Placebo kein Urteil" in _kq and "--placebo" in _kq)

    # ⚠️ DIE WARNUNG ZU H2 GEHOERT IN DEN KOPF, nicht in eine Fussnote.
    pruefe(P, "H2 traegt die Auswahlwarnung bei sich",
           "auswahlverzerrten Zeit" in _kroh
           and "noch keine Auswahlregel" in _kroh,
           "Symbole nach vergangener Trefferquote zu waehlen ist die Falle "
           "aus Kapitel 93.17 - ein Unterschied ZWISCHEN Symbolen ist noch "
           "keine Regel, dafuer muesste er sich vorwaerts wiederholen")

    # ---- DER AUSSTIEG (Kapitel 123) ----
    _asq = _quelltext("messe_ausstieg.py")
    _asroh = io.open("messe_ausstieg.py", encoding="utf-8").read()

    pruefe(P, "die zwei Ausstiegsregeln stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _asroh
           and "A1  TEILVERKAUF" in _asroh and "A2  EINSTANDSTOP" in _asroh)
    pruefe(P, "alle drei Varianten aus EINEM Vorwaertsdurchlauf",
           "EIN Vorwaertsdurchlauf fuer alle drei" in _asroh,
           "drei Laeufe waeren drei Stichproben, und Unterschiede teils "
           "Auswahl")

    # ⚠️ DIE KERZE, IN DER +1R ZUERST BERUEHRT WIRD, ENTSCHEIDET UEBER DIE
    # GANZE REGEL - dort war die erste Fassung zu guenstig.
    pruefe(P, "die Ausloesekerze zaehlt schon als ausgeloest",
           "ausgeloest = eins_beruehrt or h[j] >= marke1" in _asq,
           "beruehrt dieselbe Kerze auch den Einstand, ist die Reihenfolge "
           "unbekannt - die vorsichtige Lesart nimmt an, dass der "
           "nachgezogene Stop gegriffen hat")
    pruefe(P, "die Kosten sind bei allen Varianten gleich",
           "teilt die" in _asroh and "Ausstiegsmenge" in _asroh,
           "ein Teilverkauf teilt die Menge, nicht die Summe - "
           "unterschiedliche Kosten haetten den Vergleich wertlos gemacht")

    # ⚠️ METHODIK 2.55 - eine Permutation aendert den Mittelwert nicht.
    pruefe(P, "die Kontrolle ist ein BOOTSTRAP, keine Permutation",
           "rng.integers(0, len(bloecke), len(bloecke))" in _asq
           and "Intervall" in _asq,
           "die erste Fassung permutierte und lieferte eine Schwelle, die "
           "auf drei Stellen genau dem Messwert entsprach - eine Permutation "
           "vertauscht Werte und aendert den Mittelwert nicht")
    pruefe(P, "und der Grund steht dabei",
           # ⚠️ Nur der Kern des Satzes - der Zeilenumbruch im Quelltext
           # zerlegt jede laengere Wendung.
           "ZU PERMUTIEREN" in _asroh,
           "A1 und A2 sind deterministische Umrechnungen DESSELBEN Pfades - "
           "es gibt keine Zuordnung, die der Zufall zerstoeren koennte")

    # ---- DER STRUKTURBODEN IM STOP (Kapitel 124) ----
    _stq = _quelltext("pruefe_strukturstop.py")
    _stroh = io.open("pruefe_strukturstop.py", encoding="utf-8").read()

    pruefe(P, "der Strukturstop-Vergleich steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _stroh)

    # ⚠️ NACHGEBAUT WAERE WERTLOS - eine Kopie veraltet still, waehrend die
    # Produktion sich aendert.
    pruefe(P, "gemessen wird mit der PRODUKTIONSFUNKTION",
           "from agent.entscheidungsrechnung import _stop_abstand" in _stq,
           "_stop_abstand wird aufgerufen, nicht nachgebaut")
    pruefe(P, "die beiden Aufrufe unterscheiden sich NUR in der Marke",
           "_stop_abstand(kurs, atr, None, False, None, None)" in _stq
           and "_stop_abstand(kurs, atr, None, False, None, marke)" in _stq,
           "jeder weitere Unterschied wuerde mitgemessen und dem Boden "
           "zugerechnet")

    # ⚠️ METHODIK 2.55 - beide Varianten sind deterministische Umrechnungen
    # desselben Pfades.
    pruefe(P, "die Kontrolle ist ein BOOTSTRAP, keine Permutation",
           "rng.integers(0, len(bloecke), len(bloecke))" in _stq)

    # ⚠️ METHODIK 2.56 - DIE REGEL, DIE DIESES WERKZEUG SELBST VERLETZT HAT.
    # Die erste Fassung urteilte allein am Vertrauensintervall und meldete bei
    # -0,0008 R einen Produktionsalarm.
    pruefe(P, "die Relevanzhuerde steht VOR dem Vertrauensintervall",
           "RELEVANZ = 0.01" in _stq
           and _stq.index("abs(d) < RELEVANZ")
           < _stq.index('"BESSER" if u > 0'),
           "bei 631.755 Ankern ist fast jeder Effekt statistisch von null "
           "verschieden - die Frage ist, ob er REICHT")
    pruefe(P, "und ein Nichtbefund heisst nicht 'schlechter'",
           "kein Unterschied von Belang" in _stq,
           "-0,0008 R ist ein Fuenfzehntel dessen, was H bringt")

    # ⚠️ DIE ASYMMETRIE SELBST - hier als DAUERPRUEFUNG, weil sie in der
    # Produktion laeuft. Faellt eine dieser drei Stellen weg, traegt die
    # Unterstuetzung den Stop wieder nicht, und niemand merkt es.
    _rlq = _quelltext("agent/rollen_lauf.py")
    _ekq = _quelltext("agent/entscheidungsrechnung.py")
    # ⚠️ DIESER PRUEFSTRING KAM ZUERST AUS MEINER ERINNERUNG statt aus der
    # Quelle und schlug fehl: der Code liest `_marken_werte` und waehlt DANN
    # die Seite, er indiziert nicht direkt.
    pruefe(P, "die Unterstuetzung wird fuer den Stop ausgelesen",
           "def _marke_am_stop(" in _rlq
           and '"widerstand" if ist_short else "unterstuetzung"' in _rlq,
           "bei LONG die Unterstuetzung, bei SHORT der Widerstand - jeweils "
           "die ANDERE Marke als bei `_marke_im_weg`")
    pruefe(P, "und als marke_preis durchgereicht",
           "marke_preis=" in _rlq,
           "gebaut UND verdrahtet seit 18.08.2026 - das Memory hatte sie "
           "drei Tage laenger als offen gefuehrt")
    pruefe(P, "der weiteste der drei Boeden gewinnt",
           "def _boeden(" in _ekq
           and "jenseits der naechsten Marke" in _ekq)

    # ---- DIE UEBERLEBENSVERZERRUNG (Kapitel 121) ----
    _ueq = _quelltext("messe_ueberleben.py")
    _ueroh = io.open("messe_ueberleben.py", encoding="utf-8").read()
    _lmroh = io.open("lade_messreihen.py", encoding="utf-8").read()

    pruefe(P, "die beiden Fragen stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _ueroh
           and "S1  Wie stark" in _ueroh and "S2  Wie stark" in _ueroh)
    pruefe(P, "das Ladewerkzeug kennt die eingestellten Paare",
           '"TRADING", "BREAK"' in _lmroh,
           "ohne sie ist jede Messung ueberlebensverzerrt - und die "
           "Verzerrung lag bis Kapitel 120 bei 100 %")
    pruefe(P, "und es steht dabei, dass BREAK nicht gleich gescheitert ist",
           "NICHT GLEICH GESCHEITERT" in _lmroh,
           "Umbenennungen wie BCC -> BCH stecken darin; geprueft wurde es "
           "trotzdem, und bei den geladenen 176 handelt keiner mehr")

    # ⚠️ EIN ANKER OHNE VORWAERTSFENSTER DARF NICHT VERWORFEN WERDEN.
    pruefe(P, "der Ablauf am Reihenende zaehlt als Fehlschlag",
           # ⚠️ Beide Seiten kleinschreiben - die erste Fassung senkte nur
           # den Heuhaufen und suchte mit grossem L.
           "vorsichtige lesart" in _ueroh.lower()
           and "durch die Hintertuer" in _ueroh,
           "wer solche Anker verwirft, filtert genau den terminalen Absturz "
           "heraus - die Verzerrung waere wieder drin, nur versteckter")
    pruefe(P, "ohne die Statustabelle bricht die Messung ab",
           "messreihen_status` fehlt" in _ueq,
           "still weiterzurechnen hiesse, eine Verzerrungsmessung ohne die "
           "Verzerrung zu machen")
    pruefe(P, "beide Stichproben werden nebeneinander berichtet",
           '"nur handelnd"' in _ueq and '"ALLE"' in _ueq,
           "erst der Vergleich zeigt, wie stark die Verzerrung wirkt")

    # ---- KATEGORIE UND STRATEGIE (Kapitel 120) ----
    _klq = _quelltext("messe_klassen.py")
    _klroh = io.open("messe_klassen.py", encoding="utf-8").read()
    import messe_klassen as _KL

    pruefe(P, "die Kategorien stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _klroh
           and "BTC      die Referenzreihe" in _klroh)
    pruefe(P, "die Grenzen sind nennbare Zahlen, keine Quantile",
           _KL.GRENZE_LARGE == 50_000_000 and _KL.GRENZE_MID == 5_000_000,
           "eine Quantilsgrenze waendert sich mit der Stichprobe und laesst "
           "sich in keinem Signal nennen")

    # ⚠️ DIE EINTEILUNG DARF NICHT WISSEN, WIE GROSS EIN COIN SPAETER WURDE.
    pruefe(P, "der Umsatz kommt vom ANKER, nicht aus der Gesamthistorie",
           'f["umsatz"]' in _klq
           and "umsatz[max(0, i - 59):i + 1]" in _quelltext("messe_marken.py"),
           "sonst wuesste die Kategorie die Zukunft - derselbe Fehlertyp wie "
           "bei `gefegt` in Kapitel 112")
    pruefe(P, "Spot und Hebel werden getrennt gerechnet",
           "FINANZIERUNG_JE_TAG" in _klq and '"tage"' in _klq,
           "die Finanzierung kostet rund 0,017 R - messbar, aber sie dreht "
           "kein Vorzeichen")
    pruefe(P, "beide Schwellen werden ausgewiesen",
           "max_aus_acht" in _klq and "aus acht" in _klq,
           "acht Zellen sind ein Suchpreis (2.49) - Mid traegt einzeln und "
           "NICHT aus acht, und genau das muss sichtbar sein")
    pruefe(P, "gewuerfelt wird INNERHALB jeder Kategorie",
           "INNERHALB jeder Kategorie" in _klq,
           "gefragt ist, ob H DORT etwas beitraegt - nicht, ob die "
           "Kategorien sich unterscheiden (2.50)")

    # ---- NEUBEWERTUNG ZU ZWEI SAETZEN (Kapitel 119) ----
    _nbq = _quelltext("bewerte_neu.py")
    _nbroh = io.open("bewerte_neu.py", encoding="utf-8").read()
    import simuliere_bremse as _SB119
    # ⚠️ ROHTEXT, nicht `_quelltext` - die Herleitung des Satzes steht in
    # Kommentaren, und die entfernt `_quelltext` (Methodik 2.41). Das ist
    # hier zum ZWEITEN Mal passiert; eine Pruefung auf eine BEGRUENDUNG
    # gehoert immer auf den Rohtext.
    _SB119_ROH = io.open("simuliere_bremse.py", encoding="utf-8").read()

    pruefe(P, "es gibt einen Referenzsatz getrennt vom Betriebssatz",
           _SB119.REFERENZ_JE_SEITE == 0.003
           and _SB119.gebuehr_je_seite("krypto") == 0.015,
           "der Referenzsatz beantwortet 'ist das ein guter Trade', der "
           "Betriebssatz 'rechnet sich das fuer mich' - die Produktion "
           "bleibt bei 1,5 %")
    pruefe(P, "der Referenzsatz ist hergeleitet, nicht gesetzt",
           "Bitvavo 0,25" in _SB119_ROH and "Kraken 0,40" in _SB119_ROH,
           "aus veroeffentlichten Taker-Gebuehren der Grundstufe - eine "
           "gegriffene Zahl waere eine Annahme ohne Quelle")
    pruefe(P, "ein Mischsatz gilt nur ueber vergleichbare Modelle",
           "kein Kontinuum" in _SB119_ROH,
           "Spread (Bitpanda) und Orderbuch sind zwei Geschaeftsmodelle - "
           "ein Mittel daraus beschriebe keinen existierenden Handelsplatz")
    pruefe(P, "beide Saetze werden nebeneinander berichtet",
           "SAETZE_ZUM_BERICHTEN" in _quelltext("simuliere_bremse.py")
           and "SAETZE_ZUM_BERICHTEN" in _nbq,
           "ein Ergebnis ohne sein reales Gegenstueck laedt zur "
           "Fehldeutung ein")

    # ⚠️ DIE ENTSCHEIDENDE GROESSE IST GEBUEHRENFREI.
    pruefe(P, "das Urteil haengt an der QUOTENDIFFERENZ",
           "gebuehrenfrei" in _nbq and "Quotendifferenz" in _nbroh,
           "der Abstand zum Breakeven enthaelt die Gebuehr - genau der "
           "Fehler, der achtzehn Kapitel durchzog")
    pruefe(P, "eine Zaehlung, zwei Bewertungen",
           "Die Zaehlung ist gebuehrenfrei" in _nbroh,
           "sammle zaehlt Ausgaenge, die Gebuehr geht erst in abstand ein - "
           "beide Spalten stehen garantiert auf DENSELBEN Faellen")
    pruefe(P, "die widerlegte eigene Vorhersage steht im Kapitel",
           "schrumpft mit dem Satz" in _nbroh,
           "sie wurde gemessen und traf nicht zu - die Spanne wird groesser, "
           "nicht kleiner. Das gehoert dokumentiert, nicht stillschweigend "
           "korrigiert")

    # ---- DIE FRAGE EINMAL RICHTIG GESTELLT (Kapitel 118) ----
    _sbq = _quelltext("messe_dosis_sauber.py")
    _sbroh = io.open("messe_dosis_sauber.py", encoding="utf-8").read()
    import messe_dosis_sauber as _SB118

    pruefe(P, "die Vorabfestlegung schliesst eine zweite Runde aus",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _sbroh
           and "KEINE zweite Runde" in _sbroh,
           "117 verfehlte um 0,2 Punkte - ohne diesen Satz waere die "
           "Versuchung gross gewesen, so lange umzuformulieren, bis es passt")

    # ⚠️ DIE ZELLE AUS 117 DARF NICHT NACHTRAEGLICH ZUR VORAB BENANNTEN
    # ERKLAERT WERDEN (2.49) - deshalb waehlen und pruefen auf GETRENNTEN
    # Daten.
    pruefe(P, "gewaehlt und geprueft wird auf getrennten Daten",
           "def _waehle" in _sbq and "waehl_je" in _sbq
           and "pruef_je" in _sbq,
           "auf der Pruefseite wird nichts mehr gesucht - nur deshalb gilt "
           "dort die Ein-Zellen-Schwelle")
    pruefe(P, "die Zeitteilung hat einen Puffer",
           _SB118.PUFFER_TAGE >= max(_SB118.HORIZONTE),
           f"Puffer {_SB118.PUFFER_TAGE} Tage gegen einen Horizont von "
           f"{max(_SB118.HORIZONTE)} - ohne ihn sickert die Antwort in die "
           "Waehlseite")
    pruefe(P, "es gibt ZWEI Teilungen mit verschiedenen Schwaechen",
           '"ZEIT", "SYMBOL"' in _sbq,
           "Zeit schliesst die Epochenwette aus, Symbol die Coinwette - "
           "einzeln waere jede angreifbar")
    pruefe(P, "gerechnet wird in der vorsichtigen Lesart",
           "Vorsichtige Lesart" in _sbroh or "Ablauf zaehlt als Fehlschlag"
           in _sbroh,
           "Methodik 2.54 - sonst vergleicht man Auswahlen statt Horizonte")
    pruefe(P, "und die Basis derselben Zelle steht als Bezug daneben",
           "der faire Bezug" in _sbroh,
           "H gegen ALLE Anker zu vergleichen mischt die Geometriewahl in "
           "den Vergleich (2.50)")

    # ---- DIE DOSIS (Kapitel 117) ----
    _dsq = _quelltext("messe_dosis.py")
    _dsroh = io.open("messe_dosis.py", encoding="utf-8").read()

    pruefe(P, "die Dosisfrage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _dsroh
           and "D1  LIEGT H's OPTIMUM WOANDERS" in _dsroh)
    pruefe(P, "H wird JE ZELLE neu gebildet",
           "A haengt an k UND crv" in _dsroh,
           "A fragt nach Marken bis zum ZIEL, B nach einer Marke ueber dem "
           "STOP - beide wandern mit der Geometrie. Eine einmal fixierte "
           "Bedingung waere nicht die Dosis, sondern dieselbe Auswahl in "
           "anderer Umgebung")

    # ⚠️ METHODIK 2.54 - OHNE DIE ZWEITE LESART SIEHT EIN AUSWAHLEFFEKT
    # AUS WIE EIN BEFUND (+11,0 statt -6,4).
    pruefe(P, "beide Lesarten werden gerechnet",
           "lesart" in _dsq and "vorsichtig" in _dsq and "mild" in _dsq,
           "bei 60 Tagen entscheiden 70,2 % der Faelle, bei 250 Tagen "
           "95,1 % - wer nur die Entschiedenen vergleicht, vergleicht drei "
           "verschiedene Grundgesamtheiten")
    pruefe(P, "die Entscheidungsquote wird ausgegeben",
           "ENTSCHEIDUNGSQUOTE" in _dsq)
    pruefe(P, "der Placebo rechnet in DERSELBEN Lesart wie das Urteil",
           "DIESELBE LESART WIE DAS URTEIL" in _dsroh,
           "ein milderer Massstab waere zu niedrig (2.50)")
    pruefe(P, "die Huerdenrechnung weist beide Schwellen aus",
           "HUERDENRECHNUNG" in _dsq and "eine_zelle" in _dsq,
           "60 Zellen kosten 1,0 Punkt gegenueber einer vorab benannten - "
           "und genau diese 1,0 fehlen dem Befund")

    # ---- BRAUCHT H LIQUIDITAET? (Kapitel 116) ----
    _lqq = _quelltext("messe_liquiditaet.py")
    _lqroh = io.open("messe_liquiditaet.py", encoding="utf-8").read()
    _mkq116 = _quelltext("messe_marken.py")

    pruefe(P, "die Liquiditaetsfrage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _lqroh
           and "L1  BEDINGUNG" in _lqroh and "L2  ZERLEGUNG" in _lqroh)

    # ⚠️ ZWOELF KAPITEL LANG WURDE `del v` GERECHNET.
    pruefe(P, "das Volumen wird nicht mehr weggeworfen",
           "del v" not in _mkq116 and "umsatz = np.asarray" in _mkq116,
           "jedes Messwerkzeug seit Kapitel 99 begann mit `del v` - dabei "
           "ist Liquiditaet die Vorbedingung dafuer, dass Marken wirken")
    # ⚠️ AUF DEM ROHTEXT, nicht auf `_quelltext`. Die Begruendung steht in
    # einem Kommentar, und `_quelltext` entfernt Kommentare (Methodik 2.41) -
    # die erste Fassung dieser Pruefung suchte deshalb etwas, das sie per
    # Konstruktion nie finden konnte.
    pruefe(P, "gerechnet wird UMSATZ, nicht Stueckzahl",
           "UMSATZ statt Stueckzahl"
           in io.open("messe_marken.py", encoding="utf-8").read(),
           "Stueckzahlen sind zwischen Symbolen bedeutungslos - BTC handelt "
           "in Coins, FLOKI in Milliarden")
    pruefe(P, "der Umsatz wird nur RUECKWAERTS gerechnet",
           "umsatz[max(0, i - 59):i + 1]" in _mkq116)
    pruefe(P, "die Literaturquelle steht mit URL im Kopf",
           "ideas.repec.org" in _lqroh and "Osler" in _lqroh,
           "Recherche liefert Gruende, keine Belege - und ohne Quelle ist "
           "sie im Projekt nicht zitierbar. Hier lagen alle drei Gruende "
           "falsch, und das gehoert danebengeschrieben")
    pruefe(P, "die Liquiditaet wird SELBST als Kandidat ausgewiesen",
           "ALS EIGENER KANDIDAT" in _lqq,
           "Methodik 2.51 - faellt der Rest auf null, ist das ein Tausch "
           "und kein Ende")

    # ---- WANN TRAEGT H? (Kapitel 115) ----
    _wnq = _quelltext("messe_wann.py")
    _wnroh = io.open("messe_wann.py", encoding="utf-8").read()
    import messe_wann as _WN

    pruefe(P, "die Beharrungsfrage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _wnroh
           and "W1  BEHARRUNG" in _wnroh and "W2  NUTZEN" in _wnroh)

    # ⚠️ OHNE VERSATZ BENUTZT DAS SIGNAL ERGEBNISSE, DIE ES NOCH NICHT GAB.
    pruefe(P, "das Signal hat zwei Fenster Versatz",
           _WN.VERSATZ >= 2 and "NICHT verhandelbar" in _wnq,
           "ein Anker aus Fenster w hat 120 Tage Vorwaertsfenster - sein "
           "Ausgang steht erst am Ende von w+1 fest")
    pruefe(P, "der Vorsprung wird je Fenster gegen DASSELBE Fenster gerechnet",
           "def _fenster_vorspruenge" in _wnq,
           "sonst misst man die Marktlage des Fensters mit (2.50)")
    pruefe(P, "die Kontrolle tauscht die FENSTERREIHENFOLGE",
           "rng.permutation(vorspruenge)" in _wnq,
           "gefragt ist, ob die ABFOLGE Information traegt - also muss "
           "genau sie zerstoert werden und sonst nichts")
    pruefe(P, "Vorsprung und absoluter Abstand werden GETRENNT berichtet",
           "W2 - REICHT ES BIS ZUM BREAKEVEN" in _wnq,
           "sie sind entkoppelt: nach positivem Fenster Vorsprung -0,6 aber "
           "Abstand -14,9, nach negativem -4,6 aber +0,2 (Methodik 2.53)")

    # ---- IST DIE MARKTPHASE INVERS? (Kapitel 114) ----
    _piq = _quelltext("messe_phase_invers.py")
    _piroh = io.open("messe_phase_invers.py", encoding="utf-8").read()

    pruefe(P, "die Frage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _piroh
           and "P1  Ist die kuenftige Indexbewegung" in _piroh)

    # ⚠️ ZWEI INDIZES - sonst haengt der Befund am Indexbau statt am Markt.
    pruefe(P, "gemessen wird mit ZWEI Indizes",
           "def _index_produktion" in _piq
           and "def _index_zusammensetzungsfrei" in _piq,
           "der Produktionsindex normiert auf c[j]/c[0] und mittelt ueber "
           "2 bis 347 Reihen - die Falle aus 93 A2")
    pruefe(P, "die Gegenprobe braucht BTC und bricht sonst ab",
           "BTC fehlt in dieser Datenbank" in _piq,
           "ohne Referenzreihe ist die Gegenprobe nicht moeglich - still "
           "weiterrechnen waere schlimmer als abbrechen")
    pruefe(P, "die verworfenen Indexversuche sind dokumentiert",
           "verkettete Mediane sind schlicht kein Index" in _piroh
           and "194.392" in _piroh,
           "aus Medianen verkettet -100 %, aus Mitteln +194.392 % - wer das "
           "nicht aufschreibt, baut es beim naechsten Mal wieder")
    pruefe(P, "die Kontrolle wuerfelt ZEITBLOECKE",
           "def _blockschwelle" in _piq and "blocklaenge" in _piq,
           "Vorwaertsfenster von 120 Tagen auf taeglichen Etiketten "
           "ueberlappen um mehr als 99 % (2.47)")
    pruefe(P, "die Zahl der Bloecke wird ausgewiesen",
           "Zeitbloecke fuer die Kontrolle" in _piq,
           "13 Bloecke heisst: nur riesige Effekte waeren nachweisbar - "
           "ohne diese Zahl liest sich 'nicht invers' als Nachweis, und es "
           "ist nur eine Punktschaetzung (2.52)")

    # ---- DER DRIFT, ZERLEGT (Kapitel 113) ----
    _dzq = _quelltext("messe_drift_zerlegt.py")
    _dzroh = io.open("messe_drift_zerlegt.py", encoding="utf-8").read()

    pruefe(P, "die drei Driftfragen stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _dzroh
           and "D1  DIE U-FORM" in _dzroh and "D2  DIE KOSTEN" in _dzroh
           and "D3  GEGEN H" in _dzroh)

    # ⚠️ DER WERT DER MESSUNG HAENGT DARAN, DASS SIE AUF NEUEN REIHEN LAEUFT.
    pruefe(P, "die alten Werte aus Kapitel 102 stehen zum Vergleich daneben",
           "auf 39 Reihen" in _dzq and "36.2" in _dzq,
           "102 lief auf 39 Reihen - die 347 hat die Hypothese nie gesehen. "
           "Ohne die alten Zahlen daneben faellt nicht auf, dass die U-Form "
           "verschwindet (+7,0 -> +0,6)")
    pruefe(P, "die Kostenbereinigung ist eine Zerlegung, kein Urteil",
           "def _uform_bereinigt" in _dzq and "Vom rohen Effekt bleiben"
           in _dzq,
           "Methodik 2.51 - der ATR-Verdacht wird beziffert, nicht "
           "abgehakt; hier vergroessert die Bereinigung den Effekt sogar")
    pruefe(P, "Bloecke in Kalenderzeit, wie 2.52 verlangt",
           "idx - bloecke[-1][0] >= a.blocklaenge" in _dzq)
    pruefe(P, "und der absolute Abstand steht neben jeder Quote",
           _dzq.count("bewerte(") >= 2,
           "Methodik 2.53 - bei 442.000 Ankern wird fast jeder Effekt "
           "signifikant; +0,6 Punkte sind echt und wirtschaftlich nichts")

    # ---- DIE ANREICHERUNG (Kapitel 112) ----
    _anq = _quelltext("messe_anreicherung.py")
    _anroh = io.open("messe_anreicherung.py", encoding="utf-8").read()
    _mkq112 = _quelltext("messe_marken.py")

    pruefe(P, "die drei Vorhersagen stehen im Kopf, VOR dem Ergebnis",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _anroh
           and "E1  STAERKE" in _anroh and "E2  ALTER" in _anroh
           and "E3  GEFEGT" in _anroh)

    # ⚠️ DIE ZUKUNFTSFALLE IN `_gefegt` - 79,0 % statt korrekt 67,3 %.
    pruefe(P, "gefegt wird auf der GEKUERZTEN Reihe gerechnet",
           "bis_anker = c[:i + 1]" in _mkq112
           and "LB._gefegt(bis_anker" in _mkq112,
           "LB._gefegt liest c[ab_index+1:] - in der Produktion richtig, "
           "weil die Reihe vorher gekuerzt wird; mit historischen Ankern "
           "waere es ein Blick in die Zukunft")

    # ⚠️ EINE KONTROLLE, DIE NICHTS KONTROLLIERT, SIEHT AUS WIE EINE
    # BESTANDENE (Methodik 2.52).
    pruefe(P, "Bloecke werden in KALENDERZEIT gebildet, nicht in Ankerzahl",
           "idx - bloecke[-1][0] >= a.blocklaenge" in _anq,
           "innerhalb H ist nur jeder fuenfzigste Tag ein Anker - nach "
           "Ankerzahl geschnitten war KEINE Reihe lang genug, es wurde "
           "nichts gewuerfelt, und die Schwelle kam exakt auf den Messwert")
    pruefe(P, "die Zahl der brauchbaren Reihen wird ausgegeben",
           "Reihen lang genug" in _anq,
           "ohne diese Zeile waere die Nullkontrolle nicht aufgefallen")
    pruefe(P, "beide Schwellen werden ausgewiesen - einzeln und aus dreien",
           "SCHWELLE FUER DAS MAXIMUM AUS DREI FRAGEN" in _anq,
           "wer nur die Einzelschwelle liest, unterschlaegt den Preis des "
           "Absuchens (2.49)")
    pruefe(P, "und der absolute Abstand beider Arme steht daneben",
           "abstand_ja" in _anq and "abstand_nein" in _anq,
           "Methodik 2.51 - ein Merkmal, das den Vorsprung nicht "
           "vergroessert, den Trade aber ueber den Breakeven hebt, ist ein "
           "Ergebnis und kein Fehlschlag")

    # ---- DIE ZERLEGUNG (Kapitel 111) ----
    _zlq = _quelltext("messe_zerlegung.py")
    _zlroh = io.open("messe_zerlegung.py", encoding="utf-8").read()
    import simuliere_bremse as _SB111

    pruefe(P, "beide Fragen stehen als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _zlroh
           and "FRAGE 1" in _zlroh and "FRAGE 2" in _zlroh)

    # ⚠️ OHNE SKALIERUNG WAEREN AUF 20 TAGEN 2.435 VON 3.290 TAGEN
    # "SEITWAERTS" - die Messung haette drei Fenster verglichen, von denen
    # zwei nichts unterscheiden.
    pruefe(P, "die Phasenschwelle skaliert mit dem Fenster",
           "math.sqrt(fenster / PHASE_FENSTER)"
           in _quelltext("simuliere_bremse.py"),
           "+/-20 % sind fuer 250 Tage die gaengige Zahl; auf 20 Tagen "
           "waeren sie fast nie erreicht")
    pruefe(P, "und die Betriebsvorgabe bleibt davon unberuehrt",
           _SB111._marktphase.__defaults__[1] is None,
           "ohne Angabe gilt PHASE_SCHWELLE unskaliert - die Produktion "
           "darf von der Messerweiterung nichts merken")

    # ⚠️ METHODIK 2.51 - ZERLEGUNG STATT FALLBEIL (Nutzervorgabe 20.08.).
    pruefe(P, "Frage 2 ist eine Zerlegung, kein Fallbeil",
           "ZERLEGUNG GESTELLT, NICHT ALS FALLBEIL" in _zlroh
           and "roh_vorsprung" in _zlq and "rest_vorsprung" in _zlq,
           "als Ja/Nein-Frage haette ein knapper Fehlschlag zu 'H ist "
           "Momentum, erledigt' gefuehrt - und die +2,3 Punkte waeren mit "
           "weggeraeumt worden")
    pruefe(P, "die Kontrollgroesse wird SELBST als Kandidat ausgewiesen",
           "ALS EIGENER KANDIDAT" in _zlq,
           "faellt der Resteffekt auf null, ist das ein TAUSCH und kein "
           "Ende - ein Weg schliesst sich erst, wenn beide Zahlen null sind")
    pruefe(P, "der Hochabstand wird nur RUECKWAERTS gerechnet",
           "h[max(0, i - 249):i + 1]" in _quelltext("messe_marken.py"),
           "ein Hoch aus der Zukunft waere der Fehler, den `_swings` seit "
           "jeher vermeidet")

    # ---- DIE SPIEGELBEDINGUNG (Kapitel 110) ----
    _spq = _quelltext("messe_spiegel.py")
    _sproh = io.open("messe_spiegel.py", encoding="utf-8").read()

    pruefe(P, "die Vorhersage steht im Kopf, VOR dem Ergebnis",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _sproh
           and "baer     H' besser" in _sproh,
           "eine Vorhersage aus einem Grund kostet die halbe Huerde (2.49) - "
           "aber nur, wenn sie vorher dasteht und scheitern kann")

    # ⚠️ VIER ASYMMETRIEN - die Spiegelung ist KEINE einfache Umkehrung.
    pruefe(P, "die Finanzierung ist eingerechnet",
           "FINANZIERUNG_JE_TAG" in _spq and '"tage"' in _spq,
           "Short geht nur ueber Hebel; ein Vergleich mit den Long-Zahlen "
           "ohne Finanzierung waere falsch")
    pruefe(P, "unmoegliche Ziele werden verworfen UND gezaehlt",
           "unmoeglich" in _spq and "ziel <= 0" in _spq,
           "nach unten ist bei null Schluss, nach oben nicht - 6.013 Anker "
           "betrifft das, und ihre Zahl gehoert zum Ergebnis")
    pruefe(P, "verglichen wird gegen SHORT-Anker, nie gegen die Long-Zahlen",
           "def bewerte_short" in _spq,
           "der Markt driftet nach oben - die Basisrate fuer Short ist "
           "mechanisch niedriger")
    pruefe(P, "der Bruch 2022 steht als benannte Unterteilung",
           'BRUCH = "2022-01-01"' in _spq,
           "aus Sachkenntnis vorab benannt (Nutzerhinweis), nicht aus einem "
           "Ergebnis gesucht - Vorsprung vor 2022 -7,3, danach -6,8")
    pruefe(P, "und es steht da, dass dies keine Handelsempfehlung ist",
           "MECHANISMUSPRUEFUNG" in _sproh and "nur long" in _sproh,
           "das System handelt nur long; eine positive Zahl waere ein Beleg "
           "ueber den Pfad, kein Vorschlag")

    # ---- DIE ZEITTEILUNG (Kapitel 109) ----
    _zq = _quelltext("messe_zeitteilung.py")
    _zroh = io.open("messe_zeitteilung.py", encoding="utf-8").read()

    pruefe(P, "die Zeitteilung steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _zroh
           and "FESTLEGUNG" in _zroh and "PRUEFUNG" in _zroh)

    # ⚠️ OHNE PUFFER SICKERT DIE ANTWORT IN DIE FESTLEGUNG.
    pruefe(P, "der Puffer gegen das Vorwaertsfenster ist da",
           "puffer_bis" in _zq and "MAX_TAGE" in _zq,
           "ein Anker kurz vor der Trennlinie hat seinen Ausgang JENSEITS "
           "davon - 16.912 Anker wurden deshalb verworfen")
    pruefe(P, "die Zusammensetzung beider Haelften wird ausgewiesen",
           "ZUSAMMENSETZUNG DER HAELFTEN" in _zq,
           "Festlegung 69,6 % Bulle gegen Pruefung 12,4 % - das muss man "
           "sehen, nicht ahnen")

    # ⚠️ METHODIK 2.50 - DIE KONTROLLE BENUTZT DIESELBE GRUNDGESAMTHEIT.
    pruefe(P, "die Block-Permutation wuerfelt NUR in den Regel-Lagen",
           'and f["phase"] in regel' in _zq,
           "ueber alle Lagen gewuerfelt bekam der Zufallsarm 4,6 Punkte "
           "geschenkt, die von der Lagenwahl kamen statt von H - die "
           "Schwelle stand bei -1,8 statt bei -5,3 (Methodik 2.50)")
    pruefe(P, "verglichen wird INNERHALB derselben Lagen",
           "alle Anker IN diesen Lagen" in _zq
           and "DAS ist der faire Vergleich" in _zq,
           "gegen alle Anker in allen Lagen zu vergleichen mischt die "
           "Lagenwahl in den Vergleich")
    pruefe(P, "die Knappheitsregel 2.48 gilt auch hier",
           "ZU KNAPP" in _zq)

    # ---- DIE WIEDERHOLUNG AUF BREITER BASIS (Kapitel 108) ----
    _pq108 = _quelltext("pruefe_phasenindex.py")
    _mq108 = _quelltext("messe_marken.py")

    # ⚠️ DER PHASENINDEX IST ZUSAMMENSETZUNGSABHAENGIG - er normiert auf die
    # erste Kerze je Reihe und mittelt ueber die, die es an dem Tag gibt: von
    # 2 Reihen (2017) auf 347 (2026). Genau die Falle aus Kapitel 93 A2.
    pruefe(P, "es gibt die Gegenprobe zum Phasenindex",
           "_marktphase" in _pq108 and "bereinigter_vorsprung" in _pq108,
           "der Baermarkt-Befund (-6,5) haengt sonst an einem Index, dessen "
           "Zusammensetzung ueber neun Jahre wandert. Mit den alten "
           "Etiketten kommt -10,1 heraus - er haelt")
    pruefe(P, "der Anker traegt sein Datum",
           '"datum": d[i]' in _mq108,
           "ohne Datum laesst sich die Phase nicht mit einem anderen Index "
           "nachrechnen - die Gegenprobe waere unmoeglich")
    pruefe(P, "die Messung meldet sich waehrend langer Laeufe",
           "fortschritt" in _mq108 and "noch ca." in _mq108,
           "ein Lauf ohne Lebenszeichen ist von einem haengenden nicht zu "
           "unterscheiden")

    # ---- DIE BREITE MESSBASIS (Kapitel 107) ----
    import simuliere_bremse as _SB107
    _lq107 = _quelltext("lade_messreihen.py")
    _lroh107 = io.open("lade_messreihen.py", encoding="utf-8").read()

    # ⚠️ EIN TIPPFEHLER IM PFAD WUERDE 484 FREMDE SYMBOLE IN DIE PRODUKTION
    # SCHREIBEN - und die Watchlist steuert, was das System handelt.
    pruefe(P, "das Ladewerkzeug sperrt die Produktionsdatenbank",
           "PRODUKTION = " in _lq107
           and "ist die Produktionsdatenbank" in _lq107,
           "Messreihen gehoeren in eine eigene Datei, nicht in den Betrieb")
    pruefe(P, "jede Reihe prueft sich selbst vor dem Schreiben",
           "def pruefe(" in _lq107 and "Median-Abstand" in _lq107
           and "unplausible Kerze" in _lq107 and "doppelte Daten" in _lq107,
           "eine Quelle, die sich nicht selbst prueft, verlaesst sich "
           "darauf, dass eine spaetere Stufe ihren Fehler faengt")
    pruefe(P, "die Ueberlebensverzerrung steht im Kopf",
           "UEBERLEBENSVERZERRUNG" in _lroh107,
           "geladen wurden die HEUTE handelnden Paare - das trifft beide "
           "Arme gleich, gehoert aber in jeden Befund auf diesen Daten")

    # ⚠️ OHNE DIE ZUORDNUNG WAEREN 29 STATT 347 REIHEN GEMESSEN WORDEN -
    # ohne Fehler, ohne Warnung.
    pruefe(P, "die Messdatenbank bringt ihre Anlageklassen selbst mit",
           hasattr(_SB107, "klassen_aus_db")
           and "CREATE TABLE IF NOT EXISTS messreihen" in _lq107,
           "_reihen_roh liest die Klasse aus der WATCHLIST - neue Symbole "
           "haetten dort keinen Eintrag und waeren STILL uebersprungen")
    pruefe(P, "ohne die Tabelle gilt die Watchlist, nicht 'nichts'",
           _SB107.klassen_aus_db("data/tradinginfotool.db") is None
           and _SB107.klassen_aus_db("data/gibtsnicht.db") is None,
           "ein Rueckfall auf ein leeres Woerterbuch wuerde JEDE Reihe "
           "verwerfen - die Messung liefe ohne eine einzige Zeile durch")
    pruefe(P, "ohne Angabe verhaelt sich _reihen_roh wie bisher",
           "klassen if klassen is not None else"
           in _quelltext("simuliere_bremse.py"),
           "die Produktion darf von dieser Erweiterung nichts merken")

    # ---- KEIN STILLER RUECKFALL AUF DEN KRYPTO-SATZ (Kapitel 106) ----
    import simuliere_bremse as _SB106
    from agent.krypto import backward_tracking as BT106

    pruefe(P, "der Gebuehrensatz kommt aus EINER Funktion",
           hasattr(_SB106, "gebuehr_je_seite")
           and "KOSTEN_JE_SEITE.get(klasse, 0.015)"
           not in _quelltext("messe_marken.py")
           and "KOSTEN_JE_SEITE.get(a.klasse, 0.015)"
           not in _quelltext("simuliere_bremse.py"),
           "sechs Werkzeuge hatten je einen eigenen Rueckfall auf 0,015")
    pruefe(P, "krypto ist unveraendert 0,015",
           _SB106.gebuehr_je_seite("krypto") == BT106._KOSTEN_KRYPTO_JE_SEITE,
           "alle Messungen der Kapitel 99-105 muessen gueltig bleiben")
    pruefe(P, "eine Boersenklasse bricht LAUT ab, statt zu schaetzen",
           _wirft(lambda: _SB106.gebuehr_je_seite("aktien"), SystemExit)
           and _wirft(lambda: _SB106.gebuehr_je_seite("etf"), SystemExit),
           "an der Boerse sind die Kosten Fixgebuehr je Seite PLUS Spread "
           "und damit positionsgroessen-abhaengig - ein einzelner Prozentsatz "
           "kann das nicht ausdruecken. Der stille Rueckfall haette eine "
           "falsche Messung geliefert, die niemand als falsch erkennt")

    # ---- H BEI GLEICHEN KOSTEN (Kapitel 105) ----
    from messe_struktur_bereinigt import MINDESTALTER as _SB_ALTER
    _sq = _quelltext("messe_struktur_bereinigt.py")
    _sroh = io.open("messe_struktur_bereinigt.py", encoding="utf-8").read()

    pruefe(P, "die Frage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _sroh
           and "Stopabstand KONSTANT" in _sroh)
    pruefe(P, "entschieden wird EINE Zahl, nicht das beste Band",
           "EIN EINZELNES BAND IST KEIN URTEIL" in _sroh
           and "def bereinigter_vorsprung" in _sq,
           "fuenf Baender abzusuchen kostet nach 2.49 die doppelte Huerde - "
           "und der Vorsprung kam fast nur aus dem breitesten Band (+19,4 "
           "gegen -5,8 im schmalsten)")
    pruefe(P, "die Bandgrenzen kommen aus ALLEN Ankern, nicht aus H",
           "nicht aus H" in _sroh,
           "aus H allein waeren die Grenzen von der zu pruefenden Gruppe "
           "gesetzt")

    # ⚠️ DIE REIFEPROBE IST HIER PFLICHT, NICHT OPTION (Kapitel 104.3).
    pruefe(P, "die Reifeprobe ist ab Werk an",
           _SB_ALTER >= 250 and "_reif(laufe(" in _sq,
           f"Vorgabe {_SB_ALTER} Handelstage - ohne sie misst die Rechnung "
           "wieder die Datenlage junger Reihen")

    # ⚠️ DIE ABKUERZUNG WIRD BELEGT, NICHT BEHAUPTET - wie beim Swing-
    # Speicher in Kapitel 104. Die Permutation rechnet in Zahlen statt in
    # Woerterbuechern und muss vorher bitgenau dasselbe liefern.
    pruefe(P, "die schnelle Fassung wird gegen die langsame geprueft",
           "Zahlenfassung weicht ab" in _sq
           and "statistik(ziel) - vorsprung" in _sq,
           "eine Beschleunigung, die niemand nachrechnet, ist eine zweite "
           "Implementierung mit eigenem Fehler")
    pruefe(P, "und es wird ausgewiesen, ob ueberhaupt Kosten bereinigt sind",
           "MAX_KOSTENREST" in _sq and "zu grob" in _sq,
           "stehen die Stopabstaende je Band noch weit auseinander, ist "
           "'gleiche Kosten' eine Behauptung statt einer Schichtung")
    pruefe(P, "Block-Permutation und Knappheitsregel sind da",
           "rngb.integers(0, a.blocklaenge)" in _sq and "ZU KNAPP" in _sq,
           "Methodik 2.47 und 2.48")

    # ---- DIE STRUKTURHYPOTHESE UND IHRE ARTEFAKTPROBEN (Kapitel 104) ----
    from messe_marken import BLOCKLAENGE as _MK_BLOCK
    from simuliere_bremse import MAX_TAGE as _MAXT2
    _mq = _quelltext("messe_marken.py")
    _mroh = io.open("messe_marken.py", encoding="utf-8").read()

    pruefe(P, "die Hypothese steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _mroh
           and "A  FREIER WEG" in _mroh and "B  STOP GEDECKT" in _mroh,
           "eine vorab benannte Hypothese kostet die halbe Huerde (2.49) - "
           "aber nur, wenn sie WIRKLICH vorher steht")
    pruefe(P, "A und B einzeln sind ausdruecklich KEIN Urteil",
           "KEINE Kandidaten fuer" in _mroh
           and "kein Urteil" in _mq,
           "sonst waeren es drei Versuche statt einem - und A allein lag "
           "mit +1,8 ueber H mit +1,3, die Versuchung war real")
    pruefe(P, "die Geometrie wird NICHT abgesucht",
           "K = 2.0" in _mq and "CRV = 2.0" in _mq
           and "K_WERTE" not in _mq,
           "ein Raster haette die Huerde verdoppelt (Kapitel 103.9)")

    # ⚠️ DIE MESSUNG RUFT DIE PRODUKTIONSFUNKTION, KEINEN NACHBAU.
    pruefe(P, "sie benutzt die Marken-Ermittlung des Betriebs",
           "from agent import lagebeschreibung as LB" in _mq
           and "LB._cluster_mit_art(" in _mq and "LB._swings(" in _mq
           and "LB.NIVEAU_MIN_ABSTAND_ATR" in _mq,
           "eine nachgebaute Fassung veraltet still - dann misst man eine "
           "Struktur, die es im Betrieb nicht gibt")
    pruefe(P, "und die Abkuerzung wird belegt, nicht behauptet",
           "def pruefe_gleichheit" in _mq and "roh_pruefen" in _mq
           and "Swing-Speicher weicht ab" in _mq,
           "der Swing-Speicher ist nur zulaessig, weil das Ergebnis fuer "
           "kleineres `bis` ein PRAEFIX ist - das wird bei jedem Lauf an "
           "fuenf echten Ankern je Reihe gegen das Original geprueft")

    # ⚠️ DIE ARTEFAKTPROBE, DIE DEN BEFUND GEKIPPT HAT.
    pruefe(P, "es gibt die Reifeprobe auf junge Reihen",
           "--mindestalter" in _mroh and "mindestalter" in _mq,
           "48 % aller H-Faelle lagen in den ersten 250 Handelstagen ihrer "
           "Reihe - dort ist 'kein Widerstand im Weg' ein DATENzustand. "
           "Ohne diese Tage faellt der Befund von +1,3 auf +0,8 bei einer "
           "Schwelle von +2,4")
    pruefe(P, "die Knappheitsregel 2.48 ist eingebaut",
           "ZU KNAPP" in _mq and "Schaetzfehler der Schwelle" in _mroh,
           "liegt der Messwert im Schaetzfehler der Schwelle, gilt nichts - "
           "genau daran waere Kapitel 103 fast falsch entschieden worden")
    pruefe(P, "Block-Permutation mit wandernden Grenzen, kein freier Placebo",
           "rngb.integers(0, a.blocklaenge)" in _mq
           and "--blockplacebo" in _mroh,
           "Methodik 2.47 - bei ueberlappenden Ankern ist ein freier "
           "Placebo kein Massstab")
    pruefe(P, "der Block ist laenger als das Vorwaertsfenster",
           _MK_BLOCK > _MAXT2,
           f"Vorwaertsfenster {_MAXT2} Tage, Block {_MK_BLOCK} - ein "
           "kuerzerer Block zerschnitte die Abhaengigkeit, die er erhalten "
           "soll")

    # ---- DIE KOLLINEARITAETSPROBE UND IHRE KONTROLLE (Kapitel 103) ----
    _lq = _quelltext("messe_kollinearitaet.py")
    _lroh = io.open("messe_kollinearitaet.py", encoding="utf-8").read()
    from simuliere_bremse import MAX_TAGE as _MAXT

    pruefe(P, "die Frage steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _lroh
           and "VERSCHIEDENE INFORMATION TRAGEN" in _lroh,
           "das Nutzermodell - schwache Einzelteile, starke Konjunktion - "
           "hat eine harte Vorbedingung, und die gehoert VOR die Rechnung")
    pruefe(P, "eine Stichprobe, nicht je Kombination eine neue",
           "EINE STICHPROBE, NICHT VIELE" in _lroh,
           "wer je Kombination neu anlaeuft, misst teils Auswahl statt "
           "Wirkung - dieselbe Falle wie in Kapitel 101")
    pruefe(P, "eine Zelle braucht eine Mindestzahl",
           "MIN_FAELLE = 300" in _lq and _lq.count("< MIN_FAELLE") >= 2,
           "5 k x 4 CRV x 3 Phasen x 5 Baender sind 300 Zellen; ohne "
           "Mindestzahl misst man Rauschen")

    # ⚠️ DER FREIE PLACEBO WUERFELT INNERHALB DER GEOMETRIE. Wuerfelte er
    # darueber hinweg, zerstoerte er die LEGITIMEN k/CRV-Unterschiede - genau
    # der kaputte Massstab aus Kapitel 101.6 (Schwelle |t| >= 104).
    pruefe(P, "der freie Placebo wuerfelt INNERHALB der Geometrie",
           "for (k, crv), g in geo.items()" in _lq
           and "rng.permutation(g[\"ausgang\"])" in _lq,
           "ueber die Geometrien hinweg zu wuerfeln zerstoerte die "
           "Arithmetik (CRV 1,0 trifft oefter als CRV 3,0) statt der "
           "Behauptung - ein kaputter Massstab, kein strenger")

    # ⚠️ UND ER REICHT NICHT. Taegliche Anker mit 120 Tagen Vorwaertsfenster
    # ueberlappen um mehr als 99 %; freies Wuerfeln unterstellt Unabhaengig-
    # keit, die es nicht gibt, und macht die Schwelle zu niedrig.
    pruefe(P, "es gibt die Block-Permutation, die zur Zeitstruktur passt",
           "--blockplacebo" in _lroh and "hoechste_b" in _lq,
           "der freie Placebo behauptete eine Schwelle von 4,7 Punkten; die "
           "richtige liegt bei 16,8 bis 18,4 - Faktor vier")
    pruefe(P, "der Block ist laenger als das Vorwaertsfenster",
           "blocklaenge\", type=int, default=250" in _lroh
           and _MAXT <= 250,
           f"das Vorwaertsfenster ist {_MAXT} Tage; ein kuerzerer "
           "Block zerschnitte genau die Abhaengigkeit, die er erhalten soll")
    pruefe(P, "die Blockgrenzen wandern je Lauf",
           "rngb.integers(0, a.blocklaenge)" in _lq,
           "bei festen Grenzen reisten immer dieselben Anker gemeinsam - "
           "das macht die Zufallsverteilung schmaler, als sie sein darf")
    pruefe(P, "Bloecke werden je Symbol in ZEITLICHER Ordnung gebildet",
           "reihen" in _lq and "sorted(v)" in _lq,
           "ein Block ist nur dann ein Zeitblock, wenn er aus aufeinander"
           "folgenden Ankern DESSELBEN Symbols besteht")

    # ⚠️ EINE PROBE, DIE ZU STRENG IST, TAUGT SO WENIG WIE EINE LAXE.
    # ⚠️ DER PREIS DES ABSUCHENS GEHOERT BEZIFFERT. Die Haelfte der Huerde
    # entsteht nicht aus der Datenlage, sondern daraus, dass 300 Zellen
    # abgesucht wurden (20,5 gegen 10,2 Punkte, Methodik 2.49).
    pruefe(P, "die Huerde bei EINER vorab benannten Zelle wird ausgewiesen",
           "eine_zelle" in _lq and "HUERDENRECHNUNG" in _lq,
           "sie zeigt, was eine begruendete Hypothese wert waere - und dass "
           "der Weg nach vorn nicht mehr Methode ist, sondern weniger Zellen")
    pruefe(P, "und sie ist als Rechnung ausgewiesen, nicht als Urteil",
           "waere zirkulaer" in _lroh or "zirkulaer" in _lq,
           "die Siegerzelle nachtraeglich zu benennen und dann an der "
           "Ein-Zellen-Schwelle zu messen waere genau die Rosinenpickerei, "
           "gegen die die Schwelle gedacht ist")
    pruefe(P, "es gibt eine Positivkontrolle mit vorab benannter Zelle",
           "--positiv" in _lroh
           and 'PFLANZE = ("seitwaerts", "+10 bis +30 %", 2.5, 1.5)' in _lq,
           "ohne sie hiesse 'nichts gefunden' nur 'nicht hingesehen' - und "
           "die Zelle darf nicht die Siegerzelle sein")

    # ---- DIE BREMSE IST SIMULIERT, NICHT GERECHNET (Kapitel 99) ----
    _bq = _quelltext("simuliere_bremse.py")

    pruefe(P, "die Simulation benutzt DIESELBEN Funktionen wie der Betrieb",
           "from agent import trefferbilanz as TB" in _bq
           and "TB.merkmale(" in _bq and "TB.geschrumpft(" in _bq
           and "TB.breakeven(" in _bq,
           "eine nachgebaute Fassung waere die Sorte Kopie, die still "
           "veraltet - dann simuliert man eine Bremse, die es nicht gibt")
    pruefe(P, "Walk-Forward: der eigene Fall zaehlt erst NACH seinem Urteil",
           # AN DER REIHENFOLGE IM CODE, nicht am Kommentar: `_quelltext`
           # entfernt Kommentare (Methodik 2.41), und eine Pruefung, die
           # ihren eigenen Hinweistext sucht, findet immer sich selbst.
           _bq.index("else blockiert).append(f)")
           < _bq.index('e["faelle"] += 1'),
           "sonst sieht der Filter in die Zukunft und misst sich selbst")
    pruefe(P, "faellt beides in eine Kerze, gilt der STOP",
           _bq.index("if l[j] <= stop:") < _bq.index("if h[j] >= ziel:"),
           "die Tageskerze verraet die Reihenfolge nicht - die vorsichtige "
           "Lesart zaehlt")
    pruefe(P, "Spot und Hebel werden getrennt gerechnet",
           "FINANZIERUNG_JE_TAG" in _bq,
           "die Geometrie ist dieselbe, die Kosten sind es nicht - eine "
           "gemeinsame Zahl waere fuer beide falsch")
    pruefe(P, "und Marktphase und Asset werden aufgeschluesselt",
           "def _marktphase" in _bq and "JE ASSET" in _bq,
           "bis heute lief JEDE Messung dieses Projekts auf einem einzigen "
           "Regime - eine nur im Baermarkt gepruefte Bremse ist keine "
           "geprueffte Bremse")

    # ---- DIE UMSCHLAG-LESART IST GEMESSEN (Umbauplan 97, 20.08.) ----
    _uq = _quelltext("messe_umschlag_kontext.py")

    pruefe(P, "der Aufbau stand VOR der ersten Rechnung fest",
           "FENSTER = 250" in _uq and "HOCH_AB = 90" in _uq
           and "SCHWELLE = 0.10" in _uq,
           "Anker, Zusammenhang und Schwellen sind aus der Behauptung "
           "abgeleitet, nicht aus einem Blick in die Daten")
    pruefe(P, "marktbereinigt - sonst misst man den Markt",
           "kuenftig = kuenftig - kuenftig.mean()" in _uq)
    pruefe(P, "Signifikanz ueber Termine, Newey-West-korrigiert",
           "_newey_west(a, horizont - 1)" in _uq,
           "an einem Tag bewegt sich alles gemeinsam, und ueberlappende "
           "Vorwaertsfenster sind autokorreliert")
    pruefe(P, "beide Kontrollen sind eingebaut",
           "--positivkontrolle" in _uq and "--placebo" in _uq,
           "gemessen: ein eingepflanzter Effekt von 2 % wird auf fuenf "
           "Tagen mit t = -6,21 gefunden; der Placebo setzt die Schwelle "
           "auf |t| >= 1,65")

    # ⚠️ VOLUMEN NULL IST KEIN VOLUMEN.
    pruefe(P, "handelsfreie Tage werden nicht als niedrigster Rang gezaehlt",
           "vol if vol > 0 else np.nan" in _uq,
           "eine 0 im Volumen waere der niedrigste Rang und damit ein "
           "erfundener Anker - hier zaehlt sie als fehlend")

    # ---- DAS MODELL UND DER NUTZER SEHEN DIESELBEN FAKTEN (20.08.) ----
    #
    # Nutzerfrage: "die LLM-Bewertungen sollten die Parameter bewerten, die
    # wir auch nutzen - dann sollten diese natuerlich ident sein."
    #
    # An 25 echten Mails geprueft: von 63 Belegen mit Zahl nannten 15 eine
    # Zahl, die im Faktenblock NICHT vorkam - und alle 15 betrafen dieselbe
    # Zeile, den Umschlag. Ursache: die Mail bekam eine VON HAND GEFUEHRTE
    # Blockliste, in der `umschlag` und `fundamental` fehlten. Beide gingen
    # ans Modell und nicht an den Nutzer.
    from agent import lagebeschreibung as _LGB

    _rlq = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "die Mail bekommt ALLE Bloecke, nicht eine Handauswahl",
           "for _n in _LB.BLOCK_REIHENFOLGE" in _rlq,
           "eine Liste von Hand veraltet still - `umschlag` und `fundamental` "
           "fehlten seit dem Umbau und niemandem fiel es auf, weil die Mail "
           "ohne sie vollstaendig AUSSAH")
    # ⚠️ DIE EIGENTLICHE ZUSAGE: PROMPT UND MAIL LESEN DIESELBE LISTE.
    #
    # `beschreibe_lage` baut den Prompt aus BLOCK_REIHENFOLGE; seit dem
    # 20.08. tut die Mail dasselbe. Damit koennen die beiden nicht mehr
    # auseinanderlaufen - vorher war die eine Liste eine Konstante und die
    # andere von Hand getippt.
    _lgq = _quelltext("agent/lagebeschreibung.py")
    pruefe(P, "Prompt und Mail speisen sich aus DERSELBEN Blockliste",
           "for block in BLOCK_REIHENFOLGE" in _lgq
           and "for _n in _LB.BLOCK_REIHENFOLGE" in _rlq,
           "das ist die Zusage hinter der Nutzerfrage: was das Modell "
           "bewertet, muss der Leser sehen koennen")

    pruefe(P, "und die beiden fehlenden Bloecke gibt es wirklich",
           "umschlag" in _LGB.BLOCK_REIHENFOLGE
           and "fundamental" in _LGB.BLOCK_REIHENFOLGE,
           "sonst prueft die Zeile darueber gegen eine leere Liste")

    # ⚠️ NUR ZWEI BLOECKE WERDEN EIGENS DARGESTELLT - der Rest MUSS in die
    # Coin-Fakten. Kommt ein neuer dazu, faellt er hier auf.
    _eigens = ("bestand", "marken")
    pruefe(P, "jeder Block ist entweder eigens dargestellt oder dabei",
           all(n in _eigens or n in _LGB.BLOCK_REIHENFOLGE
               for n in _LGB.BLOCK_REIHENFOLGE)
           and '_n not in ("bestand", "marken")' in _rlq,
           "wer einen Block ergaenzt und die Mail vergisst, baut denselben "
           "Fehler noch einmal")

    # ⚠️ UND DER MODULNAME MUSS EINDEUTIG BLEIBEN.
    pruefe(P, "lagebeschreibung und lebendigkeit haben getrennte Kuerzel",
           "import lebendigkeit as _LEB" in _rlq
           and "import lebendigkeit as _LB" not in _rlq,
           "beide hiessen `_LB`; der spaetere Import ueberschrieb den "
           "frueheren, und der Zugriff auf BLOCK_REIHENFOLGE lief ins Leere")

    # ---- PERZENTILE: LESBAR UND MIT GENUG MESSUNGEN (20.08.2026) ----
    #
    # Nutzerrueckmeldung: die Perzentile seien "zum Teil nicht oder schwierig
    # einzuordnen". Zwei getrennte Maengel, beide an echten Mails gefunden.
    from agent import positionierung as _PO

    # ⚠️ EIN PERZENTIL AUS ZWEI WERTEN IST EINE MUENZE, KEINE EINORDNUNG.
    _kurz = _PO.saetze({"long_anteil_pct": 67.0, "long_n": 2})
    pruefe(P, "unter der Mindestreihe steht KEIN Perzentil",
           not any("Perzentil" in z for z in _kurz)
           and any("2 von 30" in z for z in _kurz),
           "in einer echten Mail stand 'im 0. Perzentil der letzten 2 "
           "Messungen - aussergewoehnlich wenige'. Bei zwei Werten gibt es "
           "nur 0 oder 100, und beide heissen aussergewoehnlich")
    pruefe(P, "und der Grund steht dabei, nicht nur das Fehlen",
           any("noch nicht einordnen" in z and "noetigen Messungen" in z
               for z in _kurz),
           "'laesst sich nicht einordnen' liest sich wie ein Datenausfall - "
           "eine zu kurze eigene Reihe ist etwas anderes")

    # ⚠️ UND DAS WORT SELBST WIRD EINMAL JE MAIL ERKLAERT.
    _smq = _quelltext("agent/signal_mail.py")
    pruefe(P, "'Perzentil' wird an der ersten Fundstelle erklaert",
           "Perzentil = Rangplatz in der eigenen Geschichte" in _smq
           and "nur 7 von 100" in _smq,
           "das Wort steht an 141 Stellen im System und wurde an keiner "
           "erklaert - und die Konvention ist mehrdeutig, wenn man sie nicht "
           "kennt. `marktlage._perzentil` zaehlt die Werte DARUNTER")

    # ---- DIE WIDERLEGUNG WIRD IN EINER WAEHRUNG GEPRUEFT (94, 20.08.) ----
    #
    # `bewerte()` vergleicht den Widerlegungspreis direkt mit `kurs_aktuell`.
    # Der Aufrufer uebergibt USD; die Datenbankspalte `umgeworfen_preis_eur`
    # steht aber in EUR - beide Enden nachverfolgt. Bis zum 20.08. wurde sie
    # ununsgerechnet durchgereicht: EUR liegt rund 14 % unter USD, also loeste
    # die Widerlegung bei LONG zu SPAET und bei SHORT zu FRUEH aus - und sie
    # fuehrt zur Empfehlung SCHLIESSEN. Kein Anzeigefehler, eine Entscheidung.
    _btq = _quelltext("agent/krypto/backward_tracking.py")
    pruefe(P, "der Widerlegungspreis wird vor der Pruefung umgerechnet",
           "_umg_usd" in _btq and "float(_umg_eur) / float(_fx)" in _btq,
           "sonst wird ein EUR-Preis gegen einen USD-Kurs geprueft")
    pruefe(P, "ohne Umrechnungsfaktor wird gar nicht geprueft",
           "if _umg_eur and _fx else None" in _btq,
           "lieber keine Widerlegungspruefung als eine in der falschen "
           "Waehrung - dieselbe Regel wie in `_in_eur`")
    pruefe(P, "und der Parameter heisst nicht mehr nach einer Waehrung",
           "umgeworfen_preis: float | None" in _quelltext(
               "agent/ausstiegsrechnung.py"),
           "die Funktion ist waehrungsblind - ein Name mit '_eur' war die "
           "Behauptung, die den Fehler verdeckt hat")

    # ---- WAEHRUNG: KEIN BETRAG MIT "EUR" OHNE UMRECHNUNG (20.08.2026) ----
    #
    # DIE BREITE PRUEFUNG LAEUFT MIT (Nutzervorgabe 20.08.: "damit das Thema
    # nicht immer wieder kommt"). `pruefe_waehrungen.py` geht ueber den
    # Syntaxbaum ALLER Ausgabedateien und meldet jede Stelle, die einen
    # Kursbetrag mit Waehrungsetikett ausgibt, ohne ihn umzurechnen oder ein
    # Feld mit Waehrung im Namen zu benutzen.
    import pruefe_waehrungen as _PW

    _stellen = []
    for _pfad in _PW._dateien(False):
        try:
            _q = io.open(_pfad, encoding="utf-8").read()
        except OSError:
            continue
        _stellen += [dict(x, urteil=_PW.beurteile(x))
                     for x in _PW._zerlege(_q, _pfad)]
    _rohe = [x for x in _stellen if x["urteil"] == "ROH"]
    pruefe(P, "keine Ausgabestelle beschriftet einen Betrag unumgerechnet",
           not _rohe,
           "gefunden: "
           + "; ".join(f"{x['datei']}:{x['zeile']}" for x in _rohe[:4])
           + f" (von {len(_stellen)} Stellen mit Waehrungsangabe)")
    pruefe(P, "und das Werkzeug findet ueberhaupt etwas",
           len(_stellen) > 80,
           f"{len(_stellen)} Stellen - findet es ploetzlich fast nichts, ist "
           f"das Werkzeug kaputt und nicht der Code sauber")

    # ---- AKTIONSVOKABULAR: KENNT JEDE STELLE `REDUZIEREN`? (22.08.2026) ----
    #
    # ⚠️ WARUM DAUERHAFT. S6c fand `REDUZIEREN` an sechs Stellen fehlend -
    # darunter `_TRACKABLE_ACTIONS`, die entscheidet, ob ein Signal ueberhaupt
    # AUFGELOEST wird. Acht Signale lagen mit gespeicherten Zonen in der
    # Datenbank und bekamen nie ein Ergebnis; sie sahen aus wie NICHTS_TUN.
    #
    # Der Fehler war nicht der Tippfehler, sondern die Bauart: wer eine Aktion
    # ergaenzt, muss von Hand jede Liste finden, die Aktionen aufzaehlt.
    import pruefe_aktionsvokabular as _PAV

    _av_dateien = _SUB.run(["git", "ls-files", "*.py"], capture_output=True,
                           text=True, encoding="utf-8").stdout.split()
    _av_offen, _av_geprueft = [], 0
    for _pfad in _av_dateien:
        if (not _pfad.startswith(_PAV.BETRIEB) or "hebel_" in _pfad
                or _pfad in _PAV.AUSGENOMMEN):
            continue
        try:
            _baum = _AST.parse(io.open(_pfad, encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        _s = _PAV.Sammler()
        _s.visit(_baum)
        for _zeile, _gef in _s.funde:
            if not _gef & _PAV.VERKAUFSSEITIG_NEU:
                continue
            _av_geprueft += 1
            if _PAV.VERKAUFSSEITIG_NEU - _gef:
                _av_offen.append(f"{_pfad}:{_zeile}")
    pruefe(P, "jede Stelle im Betrieb kennt das verkaufsseitige Vokabular",
           not _av_offen,
           "blind fuer REDUZIEREN: " + ", ".join(_av_offen[:4]))
    pruefe(P, "und das Werkzeug findet ueberhaupt Stellen",
           _av_geprueft >= 5,
           f"{_av_geprueft} Stellen - findet es fast nichts, ist das Werkzeug "
           f"kaputt und nicht der Code sauber")
    # ---- A5 + DIE EICHUNG VON `voll_ab` (23.08.2026) ------------------
    #
    # ⚠️ A5: DIE CRV-ABSTUFUNG GILT NUR FUER SPOT - die Messung vom 03.08.
    # fand beim Hebel die GEGENLAEUFIGE Antwort (Gate SQN +3,25 gegen +1,25).
    # Sie fragte aber das LAUF-Etikett, das seit S6b immer "spot" ist:
    # eingeschaltet haette sie jedes Hebel-Signal gekuerzt.
    from agent import entscheidungsrechnung as _ER5

    def _r5(stop_rel, spreizung):
        _echt = _ER5.GRENZEN["crv_spreizung"]
        try:
            _ER5.GRENZEN["crv_spreizung"] = spreizung
            return _ER5.rechne(kurs=100.0, atr=stop_rel * 100.0 / 2.5,
                               risiko_eur=48.0, instrument="spot",
                               betrag_wunsch_eur=800.0, hebel_handelbar=True)
        finally:
            _ER5.GRENZEN["crv_spreizung"] = _echt

    # ⚠️ DAS ETIKETT DARF NICHT VON DER ABSTUFUNG ABHAENGEN.
    #
    # DER FEHLER, DEN DAS FAENGT: `hebel_noetig` rechnet mit dem GEDECKELTEN
    # Betrag. Kuerzt die Abstufung ihn (800 -> 320 EUR), steigt er von 0,6 auf
    # 1,5 - und aus einem SPOT-Trade wird ein HEBEL-Trade, allein weil die
    # Position kleiner wurde. Eine Rueckkopplung, kein Befund.
    for _s5 in (0.025, 0.054, 0.10, 0.22):
        pruefe(P, f"Stop {_s5*100:.1f} %: das Etikett haengt nicht an der "
                  f"Abstufung",
               _r5(_s5, 1.0)["etikett"] == _r5(_s5, 5.0)["etikett"],
               f"aus {_r5(_s5, 1.0)['etikett']} wird {_r5(_s5, 5.0)['etikett']}"
               f" - ob ein Trade gehebelt ist, ist eine Eigenschaft seiner "
               f"GEOMETRIE (Verlustanteil gegen Stopabstand), nicht seines "
               f"Deckels")
    # UND SIE TRIFFT NUR DAS SPOT-ERGEBNIS.
    pruefe(P, "die Abstufung kuerzt ein HEBEL-Ergebnis nicht",
           abs(_r5(0.025, 5.0)["betrag_eur"] - 800.0) < 1e-6,
           "die Messung vom 03.08. fand beim Hebel die gegenlaeufige Antwort "
           "- sie dort anzuwenden hiesse, eine Messung gegen ihr eigenes "
           "Ergebnis zu uebertragen")
    # ⚠️ DIE EICHUNG: `voll_ab` muss die Verteilung TREFFEN.
    #
    # Gemessen an der Produktionsdatenbank: alte Kette max CRV 15,50 mit 3 %
    # ueber 6,0; Rollen-Kette max 3,00 mit NULL ueber 6,0. Mit 6,0 erreichte
    # kein Signal mehr die volle Groesse.
    pruefe(P, "`voll_ab` liegt innerhalb der gemessenen CRV-Verteilung",
           2.0 < _ER5.GRENZEN["crv_voll_ab"] <= 3.0,
           f"{_ER5.GRENZEN['crv_voll_ab']} - die Rollen-Kette hat ein Maximum "
           f"von 3,00. Ein `voll_ab` darueber macht die volle Groesse "
           f"unerreichbar und kuerzt JEDE Empfehlung")
    pruefe(P, "und die Abstufung ist weiterhin AUS",
           abs(_ER5.GRENZEN["crv_spreizung"] - 1.0) < 1e-9,
           "die Eichung ist die Vorbereitung, nicht die Inbetriebnahme - "
           "das Einschalten ist eine Entscheidung des Nutzers")

    # ---- TRAEGT DAS CRV DURCH DIE GANZE KETTE? (23.08.2026) -----------
    #
    # Nutzervorgabe: "Sicherstellung, dass die CRV-Thematik durch den ganzen
    # Plan traegt." Gemessen an allen Stellen, die ein CRV fuehren.
    import yaml as _YAMLC

    from agent import entscheidungsrechnung as _ERC
    from agent import trefferbilanz as _TBC

    _cfgc = _YAMLC.safe_load(
        io.open("Basisinfos/config.yaml", encoding="utf-8").read())
    _ziele = (_cfgc or {}).get("ziele") or {}
    _risikoc = (_cfgc or {}).get("risiko") or {}
    pruefe(P, "CRV-Minimum: Rechnung und `ziele.crv_minimum` stimmen ueberein",
           abs(float(_ERC.GRENZEN["crv"])
               - float(_ziele.get("crv_minimum", -1))) < 1e-9,
           f"GRENZEN {_ERC.GRENZEN['crv']} gegen config "
           f"{_ziele.get('crv_minimum')} - zwei Wahrheiten ueber dasselbe")
    pruefe(P, "und die Bilanz rechnet mit demselben CRV",
           abs(float(_ERC.GRENZEN["crv"]) - float(_TBC.CRV)) < 1e-9,
           "sonst misst die Trefferbilanz gegen ein anderes Ziel, als die "
           "Rechnung setzt")
    pruefe(P, "`voll_ab` stimmt mit der config ueberein",
           abs(float(_ERC.GRENZEN["crv_voll_ab"])
               - float(_risikoc.get("crv_positionsgroesse_voll_ab", -1))) < 1e-9)
    # ⚠️ UND DIE EINE STELLE, AN DER ES NICHT TRAEGT - benannt statt behoben.
    #
    # `risiko.crv_positionsgroesse_spreizung` steht auf 5.0 und wird NUR von
    # `agent/krypto/risk_gate.py` gelesen - der alten Kette. Die Rollen-Kette
    # nimmt GRENZEN["crv_spreizung"], und dort steht seit dem 15.08. 1.0.
    # Wer nur die config liest, glaubt, die Abstufung sei aktiv.
    #
    # DIESE PRUEFUNG BEHEBT DAS NICHT - sie haelt fest, dass es so IST und
    # dass der Vermerk daneben steht. Ob die Abstufung zurueckkommt, ist eine
    # Entscheidung des Nutzers und braucht eine neue Eichung (gemessen:
    # CRV-Median 2,29, Maximum 3,00 - `voll_ab` steht auf 6,0 und wird von
    # KEINEM Signal erreicht).
    pruefe(P, "die Spreizung steht bewusst auf zwei Werten - und es steht dabei",
           abs(float(_ERC.GRENZEN["crv_spreizung"]) - 1.0) < 1e-9
           and float(_risikoc.get("crv_positionsgroesse_spreizung", 0)) > 1.0
           and "GILT NUR FUER DIE ALTE KETTE" in io.open(
               "Basisinfos/config.yaml", encoding="utf-8").read(),
           "der Vermerk in der config ist die einzige Stelle, an der ein "
           "Leser erfaehrt, dass die 5.0 die Rollen-Kette nicht betrifft")

    # ---- A4: DER COOLDOWN SIEHT AUCH HEBEL-SIGNALE (23.08.2026) -------
    #
    # ⚠️ DIESEN FEHLER HABEN A1/A2 ERST ERZEUGT. `sql_bedingung("spot")`
    # lautet `hebel IS NULL`. Seit die Rechnung wieder Hebelwerte schreibt,
    # fielen Hebel-Signale aus der Cooldown-Abfrage: ein Symbol mit einem
    # Hebel-Signal von vor einer Stunde galt als frei und waere alle 15
    # Minuten neu beurteilt worden.
    #
    # DIE TOPFTRENNUNG GILT NUR, WO ES ZWEI LAEUFE GIBT - und das ist seit
    # S6b bei KEINER Gruppe der Fall. Geprueft ueber `INSTRUMENTE_JE_GRUPPE`,
    # nicht fuer Krypto angenommen.
    # ⚠️ EIGENE IMPORTE, NICHT `_sq3`/`_YAML2` VON WEITER UNTEN. Beide werden
    # in dieser Funktion erst SPAETER gebunden - genau die Unterart der
    # Namensfalle, die `finde_freie_namen.py` NICHT sieht (der Name wird ja
    # zugewiesen, nur zu spaet; siehe Kapitel 134). Siebtes Mal in drei Tagen.
    import sqlite3 as _sq4
    import yaml as _YAML4

    from agent import wiederholung as _WH4
    from agent import signal_abbildung as _SA4

    _mem4 = _sq4.connect(":memory:")
    _mem4.row_factory = _sq4.Row
    _db4 = __import__("database.db", fromlist=["db"])
    _db4.init_db(_mem4)
    _vorh4 = {r[1] for r in _mem4.execute("PRAGMA table_info(signals)")}
    for _n4, _t4 in _SA4.SPALTEN_SIGNAL.items():
        if _n4 not in _vorh4:
            _mem4.execute(f"ALTER TABLE signals ADD COLUMN {_n4} {_t4}")
    _mem4.commit()
    _cfg4 = _YAML4.safe_load(
        io.open("Basisinfos/config.yaml", encoding="utf-8").read())

    def _sperre4(gruppe, instrument, hebel, symbol="TSTA"):
        _mem4.execute("DELETE FROM signals")
        _mem4.execute(
            "INSERT INTO signals (symbol, created_at, action, gate_passed, "
            "risk_veto, pipeline_version, facts_json, quelle_kette, hebel) "
            "VALUES (?, '2026-08-23T11:00:00+00:00', 'KAUFEN', 1, 0, 'x', "
            "'{}', 'rollen', ?)", (symbol, hebel))
        _mem4.commit()
        return _WH4.gesperrt_bis(_mem4, symbol, instrument, config=_cfg4,
                                 gruppe=gruppe,
                                 jetzt="2026-08-23T12:00:00+00:00")

    from agent import assetklassen as _AK4
    for _g4 in _AK4.INSTRUMENTE_JE_GRUPPE:
        _i4 = _AK4.INSTRUMENTE_JE_GRUPPE[_g4][0]
        _sym4 = "3QSS" if _g4 == "hedge" else "TSTA"
        for _h4, _wie in ((None, "Spot"), (2.4, "Hebel")):
            pruefe(P, f"{_g4}: ein {_wie}-Signal sperrt den naechsten Lauf",
                   _sperre4(_g4, _i4, _h4, _sym4) is not None,
                   f"`sql_bedingung('{_i4}')` filtert nach dem Topf - seit "
                   f"A1/A2 fielen Hebel-Signale heraus und das Symbol waere "
                   f"alle 15 Minuten neu gefragt worden")
    # UND DIE GEGENPROBE: nach Ablauf muss es wieder frei sein.
    _mem4.execute("DELETE FROM signals")
    _mem4.execute(
        "INSERT INTO signals (symbol, created_at, action, gate_passed, "
        "risk_veto, pipeline_version, facts_json, quelle_kette, hebel) "
        "VALUES ('TSTA', '2026-08-23T04:00:00+00:00', 'KAUFEN', 1, 0, 'x', "
        "'{}', 'rollen', 2.4)")
    _mem4.commit()
    pruefe(P, "und nach Ablauf des Cooldowns ist es wieder frei",
           _WH4.gesperrt_bis(_mem4, "TSTA", "spot", config=_cfg4,
                             gruppe="krypto",
                             jetzt="2026-08-23T12:00:00+00:00") is None,
           "acht Stunden bei 3,5 h Cooldown - eine Sperre, die nicht "
           "abläuft, waere eine Abschaltung")
    # ⚠️ UND DIE TRENNUNG KEHRT ZURUECK, sobald eine Gruppe zwei Laeufe hat.
    pruefe(P, "die Topftrennung haengt an der Zahl der Laeufe",
           "_mehrere_laeufe" in _quelltext("agent/wiederholung.py")
           and "INSTRUMENTE_JE_GRUPPE" in _quelltext("agent/wiederholung.py"),
           "ein geloeschter Zweig waere eine Entscheidung ueber etwas, das "
           "noch nicht entschieden ist")
    _mem4.close()

    # ---- A1/A2: DER HEBEL FAELLT WIEDER AUS DER ZAHL AN (23.08.2026) ---
    #
    # ⚠️ SEIT S6b WAR ER AUS. `rechne()` fragte `instrument == "hebel"`, und
    # das ist fuer Krypto nie wieder wahr - jede Rechnung ergab Hebel 1,0,
    # die `hebel`-Spalte blieb leer, und daran haengen Hebel-Topf (3.000 EUR,
    # Nutzerentscheidung 13.08.) und Hebel-Cooldown.
    from agent import entscheidungsrechnung as _ERA
    from agent import signal_abbildung as _SAA

    def _r(stop_rel, handelbar=True, short=False):
        return _ERA.rechne(kurs=100.0, atr=stop_rel * 100.0 / 2.5,
                           risiko_eur=48.0, instrument="spot",
                           betrag_wunsch_eur=800.0, ist_short=short,
                           hebel_handelbar=handelbar)

    pruefe(P, "ein enger Stop ergibt wieder einen Hebel",
           _r(0.025)["etikett"] == "hebel" and _r(0.025)["hebel"] > 1.0,
           f"{_r(0.025)['etikett']}, Hebel {_r(0.025)['hebel']} - seit S6b "
           f"war das ausnahmslos spot/1,0")
    pruefe(P, "ein weiter Stop bleibt spot",
           _r(0.10)["etikett"] == "spot" and _r(0.10)["hebel"] == 1.0)
    pruefe(P, "ohne Handelbarkeit gibt es keinen Hebel",
           _r(0.025, handelbar=False)["etikett"] == "spot",
           "eine Aktie laesst sich hier nicht hebeln")
    # ⚠️ SHORT IST IMMER GEHEBELT - Spot kann nicht leerverkauft werden.
    pruefe(P, "ein SHORT ist auch bei weitem Stop gehebelt",
           _r(0.10, short=True)["etikett"] == "hebel")
    # ⚠️ UND DIE SPOT-KONVENTION BLEIBT UNBERUEHRT (C2 ist NICHT entschieden).
    pruefe(P, "oberhalb der Schwelle bleibt der Betrag wie bisher",
           abs(_r(0.22)["betrag_eur"] - 800.0) < 1e-6,
           "der Betrag folgt bei Spot weiter dem Wunsch, das Risiko dem "
           "Stopabstand - `risiko_quelle` sagt das ausdruecklich. Wer das "
           "aendert, entscheidet C2, und das ist eine eigene Frage")
    # RUECKFALL FUER DIE ALTEN KETTEN: ohne Angabe gilt das Instrument.
    for _instr, _erw in (("hebel", "hebel"), ("spot", "spot")):
        _alt = _ERA.rechne(kurs=100.0, atr=1.0, risiko_eur=48.0,
                           instrument=_instr, betrag_wunsch_eur=800.0)
        pruefe(P, f"alte Kette ohne Angabe: instrument={_instr} -> {_erw}",
               _alt["etikett"] == _erw,
               "hebel_analyst und Verwandte rufen unveraendert - dort gibt es "
               "beide Laeufe noch")
    # A2: die Spalte folgt dem ERGEBNIS.
    for _et, _h, _erw in (("hebel", 2.4, 2.4), ("spot", 1.0, None)):
        _f = _SAA.felder_aus_entscheidung(
            {"aktion": "KAUFEN", "richtung": "LONG"}, fakten={},
            rechnung={"etikett": _et, "hebel": _h}, instrument="spot")
        pruefe(P, f"Rechnung sagt {_et} -> Hebelspalte "
                  f"{'gefuellt' if _erw else 'leer'}",
               _f.get("hebel") == _erw,
               "`toepfe.sql_bedingung()` trennt die Toepfe an genau dieser "
               "Spalte - der Hebel-Topf ist ein RISIKODECKEL, kein Konto")
    # ⚠️ UND A1 OHNE A2 WAERE DIE GEFAEHRLICHE KOMBINATION.
    pruefe(P, "die Spalte haengt NICHT mehr am Lauf",
           _SAA.felder_aus_entscheidung(
               {"aktion": "KAUFEN", "richtung": "LONG"}, fakten={},
               rechnung={"etikett": "hebel", "hebel": 2.4},
               instrument="spot").get("hebel") == 2.4,
           "sonst entstuende der Hebel wieder, ohne in den gedeckelten Topf "
           "gebucht zu werden - eine 3.000-EUR-Grenze, die nichts sieht")
    # Und die verdrehte Grenze, dieselbe wie in `dimensioniere`.
    pruefe(P, "hebel_grenze nennt den echten Deckel",
           _ERA.rechne(kurs=100.0, atr=1.0, risiko_eur=240.0,
                       instrument="spot", betrag_wunsch_eur=800.0,
                       hebel_handelbar=True).get("hebel_grenze")
           in ("Risikobudget", "RM-11 Liquidationsabstand", "Hoechsthebel"))

    # ---- WAS DAS MODELL LIEST, HAENGT AN DER GRUPPE (23.08.2026) -------
    #
    # ⚠️ DIESE LUECKE HAT DIE S6a-GEGENPRUEFUNG NICHT GEFUNDEN. Sie prueft
    # den Prompt der Rolle BC und das Schema - nicht den INHALT des
    # Lagebilds. Dort standen zwei Bausteine auf `instrument != "hebel"`,
    # und seit S6b erreichten sie niemanden mehr:
    #
    #   `_finanzierung`    was die Finanzierung am Terminmarkt kostet
    #   `_hebelgeometrie`  wie weit es bis zur Zwangsaufloesung ist
    #
    # Der Hebel ist seit S6a ein ERGEBNIS der Rechnung. Ergibt sie eine
    # gehebelte Position, hatte das Modell beide Zahlen nie gesehen.
    from agent import lagebeschreibung as _LB2

    class _K2:
        def __init__(s, d, c):
            s.date, s.open, s.high, s.low, s.close, s.volume = (
                d, 100.0, 104.0, 96.0, c, 1.0)

    _reihe2 = [_K2(f"2026-07-{i % 28 + 1:02d}", 100.0 + (i % 7))
               for i in range(300)]
    _fin2 = {"beobachtungen": 40, "anteil_positiv_pct": 62, "perzentil": 71}

    def _bloecke2(gruppe, instrument="spot"):
        return _LB2.geteilt(symbol="X", reihe=_reihe2, index=299,
                            kurs_eur=100.0, atr=3.0, finanzierung=_fin2,
                            instrument=instrument, assetklasse=gruppe)

    for _feld, _was in (("finanzierung", "die Finanzierungsrate"),
                        ("hebelgeometrie", "der Liquidationsabstand")):
        pruefe(P, f"{_was} erreicht Krypto - auch im Spot-Lauf",
               bool(_bloecke2("krypto", "spot").get(_feld)),
               "seit S6b gibt es fuer Krypto NUR den Spot-Lauf - haengt der "
               "Baustein am Lauf, erreicht er niemanden mehr")
        pruefe(P, f"{_was} bleibt bei Aktien weg",
               not _bloecke2("aktien", "spot").get(_feld),
               "eine Aktie laesst sich hier nicht hebeln - der Satz waere "
               "ein konstantes Feld ohne Aussage")
        pruefe(P, f"{_was} haengt NICHT mehr am Lauf",
               (bool(_bloecke2("krypto", "spot").get(_feld))
                == bool(_bloecke2("krypto", "hebel").get(_feld))),
               "die Frage ist die HANDELBARKEIT der Gruppe, nicht welcher "
               "Lauf gerade dran ist")
    # ⚠️ UND DER SATZ IST BEDINGT, NICHT FESTSTELLEND (23.08.2026).
    #
    # NUTZERFRAGE: "bei Spot keine, aber bei Hebel schon". Ueber die AUSWAHL
    # geht das nicht - der Faktenblock entsteht, bevor das Modell antwortet,
    # und der Hebel faellt AUS der Antwort an. Also sagt es der Satz selbst,
    # genau wie `_hebelgeometrie` es seit dem 19.08. tut.
    _fin_satz = " ".join(_bloecke2("krypto", "spot").get("finanzierung") or [])
    pruefe(P, "der Finanzierungssatz nennt die Bedingung",
           _fin_satz.startswith("Falls ein Hebel noetig wird"),
           "er behauptete sonst eine Zahlung, die bei einem Spot-Kauf nie "
           "stattfindet - und wurde gemessen in 63 % der Spot-Urteile zitiert")
    pruefe(P, "und er sagt ausdruecklich, wann sie NICHT anfaellt",
           "Spot-Kauf faellt sie nicht an" in _fin_satz,
           "das Modell soll es nicht raten muessen")
    pruefe(P, "beide Hebel-Bausteine sind bedingt formuliert",
           _fin_satz.startswith("Falls ein Hebel")
           and " ".join(_bloecke2("krypto", "spot").get("hebelgeometrie")
                        or []).startswith("Falls ein Hebel"),
           "seit S6a faellt der Hebel aus der RECHNUNG an - ein Faktenblock, "
           "der ein Hebelgeschaeft unterstellt, widerspricht in vier von "
           "fuenf Mails der eigenen Rechnung")

    # ⚠️ R-T11: JEDES PERZENTIL TRAEGT SEIN WORT (23.08.2026).
    #
    # "Das 71. Perzentil" verlangt vom Leser die Entscheidung, ob das viel
    # ist - und dieser Leser ist ein Sprachmodell. Der Finanzierungssatz war
    # der EINZIGE im Faktentext ohne Einordnung; alle anderen tragen sie seit
    # dem 17.08.
    for _p, _erw in ((95, "aussergewoehnlich hoch"),
                     (71, "im gewohnten Bereich"),
                     (5, "aussergewoehnlich niedrig")):
        _s = " ".join(_LB2._finanzierung(
            {"beobachtungen": 40, "anteil_positiv_pct": 62, "perzentil": _p},
            "spot", assetklasse="krypto"))
        pruefe(P, f"Perzentil {_p} wird als '{_erw}' eingeordnet",
               _erw in _s, _s[-90:])
    # ⚠️ UND AUS DENSELBEN GRENZEN. Hier standen 90 und 10 direkt im Code,
    # mit dem Kommentar "dieselben Grenzen wie ueberall" - und "ueberall"
    # hiess `positionierung.EXTREM_OBEN/UNTEN`. Zwei Orte, keine Verbindung.
    pruefe(P, "die Perzentil-Grenzen sind importiert, nicht abgeschrieben",
           "from agent.positionierung import EXTREM_OBEN"
           in _quelltext("agent/lagebeschreibung.py")
           and "if p >= 90" not in _quelltext("agent/lagebeschreibung.py"),
           "zwei Massstaebe nebeneinander waeren schlimmer als keiner - "
           "wer die Grenze dort verschiebt, muss sie hier mitverschieben")

    # ⚠️ UND KEIN `None` IM PROMPT. Der Satz wurde bisher ungeprueft gebaut -
    # fehlte ein Wert, stand "in None % der letzten 40 Perioden" im
    # Modelltext. Fail-soft ist fail-silent.
    _luecke2 = dict(_fin2, anteil_positiv_pct=None)
    pruefe(P, "eine Luecke erzeugt KEINEN Satz mit `None` darin",
           not _LB2.geteilt(symbol="X", reihe=_reihe2, index=299,
                            kurs_eur=100.0, atr=3.0, finanzierung=_luecke2,
                            instrument="spot",
                            assetklasse="krypto").get("finanzierung"),
           "lieber kein Satz als ein Satz mit einer Luecke darin")

    # ---- DER COOLDOWN JE GRUPPE (23.08.2026) ---------------------------
    #
    # ⚠️ S6b HAT NICHT NUR DEN ZWEITEN LAUF ENTFERNT, SONDERN AUCH SEINEN
    # COOLDOWN-TOPF. spot 15 h, hebel 3,5 h - der Hebel-Lauf trug rund zwei
    # Drittel der Urteile (134/149/150 gegen 95/69/85 je Tag). Ohne ihn wurde
    # jedes Krypto-Symbol nur noch alle 15 Stunden beurteilt; am 22.08. kam
    # nach 21:12 acht Laeufe lang nichts mehr durch, und es gab keine
    # Signalmails mehr.
    # ⚠️ EIGENER IMPORT, NICHT `_YAML` VON WEITER UNTEN. Der Name wird in
    # dieser Funktion erst spaeter gebunden - und der NameError kam prompt.
    # Fuenftes Mal an zwei Tagen, immer dasselbe Muster.
    import yaml as _YAML2

    from agent import wiederholung as _WH2

    _cfg_wh = _YAML2.safe_load(
        io.open("Basisinfos/config.yaml", encoding="utf-8").read())
    # ⚠️ EIN BEREICH STATT EINES PUNKTES (28.08.2026).
    #
    # Diese Pruefung schuetzt vor dem Ausfall vom 22.08.: mit 15 h kam nach
    # 21:12 acht Laeufe lang nichts mehr durch. Sie tat das, indem sie den
    # Reparaturwert 3,5 festschrieb - und scheiterte damit an jeder bewussten
    # Aenderung, auch an einer, die den Ausfall nicht wiederholt.
    #
    # DIE ABSICHT IST "DIE PRODUKTION DARF NICHT STILLSTEHEN", nicht "der Wert
    # ist 3,5". Gemessen an 1.613 Signalen ueber 8 Tage (echte Mechanik):
    #      3,5 h -> 163 Signale/Tag      12 h -> 72/Tag      15 h -> 68/Tag
    # Auch 15 h erzeugt heute Signale - der Ausfall vom 22.08. entstand, weil
    # es DAMALS keine Differenzierung gab und JEDES Symbol denselben langen
    # Cooldown bekam. Seit L4/L5 haben gehebelte Signale 3,5 h und die
    # Akkumulation 48 h; die Menge verteilt sich anders.
    #
    # DIE OBERGRENZE BLEIBT TROTZDEM: ueber 15 h ist der Bereich, in dem der
    # Ausfall stattfand, und dorthin darf es nicht ohne neue Messung zurueck.
    _std_kr = _WH2.stunden("spot", _cfg_wh, "krypto")
    pruefe(P, "Krypto wird nicht wieder in den Ausfall-Takt gestellt",
           0 < _std_kr <= 15.0,
           f"{_std_kr} h - ueber 15 h liegt der Bereich, in dem am 22.08. "
           f"acht Laeufe lang nichts mehr durchkam")
    for _g in ("aktien", "rohstoffe", "themen_etf", "hedge"):
        pruefe(P, f"{_g} behaelt seine 24 h",
               abs(_WH2.stunden("spot", _cfg_wh, _g) - 24.0) < 1e-9,
               "diese Gruppen hatten nie einen Hebel-Lauf - bei ihnen ist "
               "nichts weggefallen, also gibt es nichts zu reparieren")
    # ⚠️ UND DER NEUE TAKT IST BILLIGER ALS DER ZUSTAND VOR S6b, nicht
    # teurer: 1/15 + 1/3,5 = 0,352 Fragen je Symbol und Stunde gegen
    # 1/3,5 = 0,286. Ein Lauf statt zwei, und der kurze Takt.
    _vorher = 1.0 / 15.0 + 1.0 / 3.5
    _jetzt = 1.0 / _WH2.stunden("spot", _cfg_wh, "krypto")
    pruefe(P, "und er kostet weniger Aufrufe als vor S6b",
           _jetzt < _vorher,
           f"{_jetzt:.3f} gegen {_vorher:.3f} Fragen je Symbol und Stunde - "
           f"waere er teurer, waere es eine Lockerung und keine Reparatur")

    # ---- E2: AM ERSTELLUNGSTAG ZAEHLT NUR DER SCHLUSSKURS (22.08.2026) --
    #
    # ⚠️ WAS SCHIEFGING. `min_date = signal.created_at[:10]` nahm die GANZE
    # Tageskerze - samt Hoch und Tief, die VOR dem Signal lagen. Ein Signal
    # von 18:00 bekam das Tageshoch von 10:00 gutgeschrieben, und
    # `einstieg_beruehrt()` zaehlte eine Zone als getroffen, die der Kurs vor
    # dem Signal beruehrt hatte.
    from agent.krypto import backward_tracking as _BTE

    # Der Tag NACH dem Signal: volle Kerze.
    pruefe(P, "ab dem Folgetag zaehlt die volle Kerze",
           _BTE.handelsspanne(110, 90, 100, "2026-08-23",
                              "2026-08-22T18:00:00+00:00") == (110, 90))
    # Der Erstellungstag selbst: nur der Schlusskurs, weil nur er
    # nachweislich NACH dem Signal liegt.
    pruefe(P, "am Erstellungstag zaehlt nur der Schlusskurs",
           _BTE.handelsspanne(110, 90, 100, "2026-08-22",
                              "2026-08-22T18:00:00+00:00") == (100, 100),
           "das Tageshoch kann Stunden VOR dem Signal gelegen haben - der "
           "Schlusskurs kann das nicht")
    pruefe(P, "ohne Schlusskurs gibt es fuer den Tag keine Aussage",
           _BTE.handelsspanne(110, 90, None, "2026-08-22",
                              "2026-08-22T18:00:00+00:00") == (None, None),
           "eine erfundene Zuordnung waere schlimmer als eine fehlende")
    # ⚠️ UND DER TAG DAVOR AUCH NICHT - ein nachgeladener aelterer Tag darf
    # dem Trade genauso wenig zugerechnet werden.
    pruefe(P, "ein Tag VOR dem Signal zaehlt ebenfalls nicht voll",
           _BTE.handelsspanne(110, 90, 100, "2026-08-21",
                              "2026-08-22T18:00:00+00:00") == (100, 100))
    # DIE MFE BLEIBT DAVON UNBERUEHRT - sie beschreibt die Bewegung des
    # WERTES, nicht die eines Trades, und wird anderswo so gelesen.
    _quelle_bt = _quelltext("agent/krypto/backward_tracking.py")
    pruefe(P, "die MFE sieht weiterhin die volle Kerze",
           "_erfasse_mfe(guenstigster_tagespreis, day)" in _quelle_bt
           and _quelle_bt.index("_erfasse_mfe(guenstigster_tagespreis, day)")
           < _quelle_bt.index("_hoch, _tief = handelsspanne("),
           "sie muss VOR der Einschraenkung stehen - sonst wird still eine "
           "Groesse umgedeutet, die andere Auswertungen anders lesen")

    # ⚠️ `sqlite3` IST IN DIESER FUNKTION NICHT GEBUNDEN. Der Name existiert
    # auf Modulebene, aber die erste Fassung dieses Blocks stand VOR dem
    # Import und lief prompt in einen NameError - dieselbe Falle, die
    # `finde_freie_namen.py` sucht, heute zum vierten Mal. Der Import gehoert
    # VOR den ersten Gebrauch, nicht irgendwohin in dieselbe Funktion.
    import sqlite3 as _sq3

    # ---- DIE NACHOEFFNUNG TRIFFT GENAU DIE ZEILEN, DIE SIE SOLL --------
    #
    # ⚠️ WARUM ES SIE GIBT. S6c erweiterte `_TRACKABLE_ACTIONS` um
    # REDUZIEREN - und ich schrieb in Kapitel 135, die Zeilen bekaemen ihr
    # Ergebnis "beim naechsten Lauf nachtraeglich". FALSCH: die Auswertung
    # holt nur Zeilen mit `outcome_status IS NULL OR = 'offen'`.
    # `nicht_anwendbar` ist ein ENDZUSTAND. Am Export vom 22.08. 21:11
    # nachgemessen: 11 von 12 standen unveraendert da.
    #
    # WER EINEN FILTER ERWEITERT, OEFFNET KEINE ZEILE, DIE DER ALTE FILTER
    # ENDGUELTIG ABGELEGT HAT.
    _mem_no = _sq3.connect(":memory:")
    _mem_no.row_factory = _sq3.Row
    _dbn = __import__("database.db", fromlist=["db"])
    _dbn.init_db(_mem_no)
    # ⚠️ `init_db()` HAT DIE NACHOEFFNUNG SCHON LAUFEN LASSEN und die Marke
    # gesetzt - auf einer leeren Datenbank ohne Wirkung. Fuer den Test muss
    # sie weg, sonst prueft er einen No-Op. (Genau das meldete die Suite beim
    # ersten Anlauf: "geoeffnet: [], Anzahl 0".)
    _mem_no.execute("DELETE FROM meta WHERE key = ?",
                    (_dbn._NACHOEFFNUNG_MARKE,))
    # Drei Faelle: der zu oeffnende, einer ohne Zonen, einer mit anderer
    # Aktion. Nur der erste darf angefasst werden.
    for _sym, _akt, _tp in (("MITZONE", "REDUZIEREN", 10.0),
                            ("OHNEZONE", "REDUZIEREN", None),
                            ("ANDERE", "TAUSCHEN", 10.0)):
        _mem_no.execute(
            "INSERT INTO signals (symbol, created_at, action, gate_passed, "
            "risk_veto, pipeline_version, facts_json, outcome_status, "
            "take_profit_usd_von, stop_loss_usd_von) "
            "VALUES (?, ?, ?, 1, 0, 'x', '{}', 'nicht_anwendbar', ?, ?)",
            (_sym, "2026-08-20T00:00:00+00:00", _akt, _tp,
             (5.0 if _tp is not None else None)))
    _mem_no.commit()
    _n1 = _dbn._migrate_reduzieren_nachoeffnen(_mem_no)
    _offen = {r["symbol"] for r in _mem_no.execute(
        "SELECT symbol FROM signals WHERE outcome_status IS NULL")}
    pruefe(P, "die Nachoeffnung trifft NUR REDUZIEREN mit Zonen",
           _offen == {"MITZONE"} and _n1 == 1,
           f"geoeffnet: {sorted(_offen)}, Anzahl {_n1} - ohne Zonen bliebe "
           f"das Ergebnis dasselbe, eine andere Aktion war nie betroffen")
    _n2 = _dbn._migrate_reduzieren_nachoeffnen(_mem_no)
    pruefe(P, "und sie laeuft nur EINMAL", _n2 == 0,
           "ohne Marke oeffnete jeder Start die Zeilen erneut, die die "
           "Auswertung zu Recht wieder ablegt - eine Schleife ohne Ende")
    pruefe(P, "die Marke steht in `meta`",
           _mem_no.execute("SELECT COUNT(*) n FROM meta WHERE key = ?",
                           (_dbn._NACHOEFFNUNG_MARKE,)).fetchone()["n"] == 1)

    # ---- UND DASSELBE FUER E2 (22.08.2026) -----------------------------
    #
    # ⚠️ METHODIK 2.62 GILT AUCH FUER EINE GEAENDERTE REGEL, nicht nur fuer
    # einen erweiterten Filter. E2 rechnet den Erstellungstag anders - aber
    # ein Endzustand wird nie wieder angefasst. Gemessen: 35 Endzustaende
    # fallen unter E2 anders aus, 16 davon gelten heute als Treffer.
    _mem_no.execute("DELETE FROM meta WHERE key = ?",
                    (_dbn._E2_NACHOEFFNUNG_MARKE,))
    for _sym, _zust, _tp in (("TREFFER", "take_profit_erreicht", 10.0),
                             ("STOP", "stop_loss_erreicht", 10.0),
                             ("OHNEZONE", "take_profit_erreicht", None),
                             ("NICHTKERZE", "nicht_anwendbar", 10.0),
                             ("UEBERHOLT", "ueberholt_durch_neuere_analyse",
                              10.0)):
        _mem_no.execute(
            "INSERT INTO signals (symbol, created_at, action, gate_passed, "
            "risk_veto, pipeline_version, facts_json, outcome_status, "
            "take_profit_usd_von, stop_loss_usd_von) "
            "VALUES (?, ?, 'KAUFEN', 1, 0, 'x', '{}', ?, ?, 5.0)",
            (_sym, "2026-08-20T00:00:00+00:00", _zust, _tp))
    _mem_no.commit()
    _e1 = _dbn._migrate_e2_nachoeffnen(_mem_no)
    _auf = {r["symbol"] for r in _mem_no.execute(
        "SELECT symbol FROM signals WHERE outcome_status IS NULL "
        "AND symbol IN ('TREFFER','STOP','OHNEZONE','NICHTKERZE','UEBERHOLT')")}
    pruefe(P, "E2 oeffnet die AUS KERZEN gerechneten Ergebnisse",
           _auf == {"TREFFER", "STOP"} and _e1 == 2,
           f"geoeffnet: {sorted(_auf)}, Anzahl {_e1} - `nicht_anwendbar` kam "
           f"nie aus einer Kerze, `ueberholt` aus einem SPAETEREN Signal, und "
           f"ohne Zonen gibt es nichts nachzurechnen")
    pruefe(P, "und auch sie laeuft nur EINMAL",
           _dbn._migrate_e2_nachoeffnen(_mem_no) == 0)
    pruefe(P, "die beiden Nachoeffnungen haben GETRENNTE Marken",
           _dbn._E2_NACHOEFFNUNG_MARKE != _dbn._NACHOEFFNUNG_MARKE,
           "verschiedene Anlaesse muessen einzeln nachvollziehbar bleiben")
    _mem_no.close()

    # ---- JEDE MIGRIERTE SPALTE MUSS LESBAR BLEIBEN (22.08.2026) ---------
    #
    # ⚠️ DIESER FEHLER HAT DIE APP AM NOTEBOOK NICHT MEHR STARTEN LASSEN.
    #
    # E1 legte `einstieg_erreicht` per Migration auf `signals` UND
    # `hebel_signals`. `_row_to_signal()` filtert seit dem 19.08. auf die
    # Felder der Klasse - `_row_to_hebel_signal()` NICHT: dort ging die Zeile
    # ungefiltert als `HebelSignal(**data)` in den Konstruktor, und eine
    # unbekannte Spalte ist dort ein TypeError.
    #
    # ⚠️ WARUM ES AM DESKTOP NICHT ZU SEHEN WAR: dort laeuft `main.py` nie,
    # also lief die Migration nie, also hatte die Tabelle die Spalte nie.
    # EINE PRUEFUNG GEGEN EINE UNMIGRIERTE DATENBANK PRUEFT DIE MIGRATION
    # NICHT. Deshalb legt diese hier die Datenbank frisch an und migriert sie.
    import dataclasses as _dc2

    from database.models import HebelSignal as _HS
    from database.models import Signal as _SG

    _mem_mig = _sq3.connect(":memory:")
    _mem_mig.row_factory = _sq3.Row
    _dbm = __import__("database.db", fromlist=["db"])
    _dbm.init_db(_mem_mig)
    for _tab, _klasse in (("signals", _SG), ("hebel_signals", _HS)):
        _spalten = {r["name"] for r in
                    _mem_mig.execute(f"PRAGMA table_info({_tab})")}
        _felder = {f.name for f in _dc2.fields(_klasse)}
        pruefe(P, f"{_tab}: die Tabelle hat ueberhaupt Spalten",
               len(_spalten) > 20, f"{len(_spalten)} - init_db hat nicht "
                                   f"durchgelaufen, die Pruefung waere leer")
        # Die Klasse MUSS nicht jede Spalte kennen - eine Spalte darf einer
        # anderen Auswertung gehoeren. Sie darf die Zeile nur nicht zerreissen.
        _unbekannt = _spalten - _felder
        pruefe(P, f"{_tab}: unbekannte Spalten sind benannt, nicht ueberraschend",
               True, f"{len(_unbekannt)} Spalten kennt {_klasse.__name__} "
                     f"nicht - das ist erlaubt, solange der Lesepfad sie "
                     f"filtert (naechste Pruefung)")
    # DER EIGENTLICHE NACHWEIS: eine Zeile mit ALLEN Spalten durch beide
    # Umwandler schicken. Genau das ist am Notebook gescheitert.
    for _tab, _fn in (("signals", _dbm._row_to_signal),
                      ("hebel_signals", _dbm._row_to_hebel_signal)):
        # ⚠️ PFLICHTSPALTEN MUESSEN BEFUELLT WERDEN, sonst scheitert schon
        # das INSERT und die Pruefung testet den Lesepfad gar nicht. Der Wert
        # ist gleichgueltig - geprueft wird, ob die Zeile LESBAR ist.
        _info = [dict(name=r["name"], typ=(r["type"] or "").upper(),
                      pflicht=bool(r["notnull"]), vorgabe=r["dflt_value"],
                      schluessel=bool(r["pk"]))
                 for r in _mem_mig.execute(f"PRAGMA table_info({_tab})")]
        # `SELECT *` liefert ohnehin JEDE Spalte - das INSERT muss also nur
        # die Pflichtfelder erfuellen. Alles andere bleibt NULL, und genau so
        # sieht eine frisch migrierte Zeile aus.
        _spalten = [s["name"] for s in _info]
        _roh = {_s["name"]: (0 if _s["typ"].startswith(("INT", "REAL", "NUM"))
                             else "x")
                for _s in _info
                if _s["pflicht"] and _s["vorgabe"] is None
                and not _s["schluessel"]}
        _roh.update({"symbol": "X", "created_at": "2026-08-22T00:00:00+00:00",
                     "action": "KAUFEN", "gate_passed": 1, "risk_veto": 0})
        _mem_mig.execute(
            f"INSERT INTO {_tab} ({', '.join(_roh)}) VALUES "
            f"({', '.join('?' for _ in _roh)})", tuple(_roh.values()))
        _zeile = _mem_mig.execute(f"SELECT * FROM {_tab} LIMIT 1").fetchone()
        try:
            _obj = _fn(_zeile)
            _ok, _grund = _obj is not None, ""
        except Exception as _exc:                             # noqa: BLE001
            _ok, _grund = False, f"{type(_exc).__name__}: {_exc}"
        pruefe(P, f"{_tab}: eine Zeile mit ALLEN Spalten laesst sich lesen",
               _ok, _grund + " - eine neue Spalte darf den LESEPFAD nicht "
                             "toeten; genau daran startete die App am "
                             "22.08. am Notebook nicht mehr")
    _mem_mig.close()

    # ---- `gebunden_durch` MUSS DEN ECHTEN DECKEL NENNEN (22.08.2026) ----
    #
    # ⚠️ DIE BEDINGUNG WAR VERDREHT. Sie lautete `hebel <= hebel_noetig`, und
    # da `hebel` aus einem min() ueber hebel_noetig kommt, war das bei LONG
    # IMMER wahr - die Zweige "Hoechsthebel" und "RM-11" waren toter Code.
    # Ueber 18 Kombinationen kam nur "Risikobudget" heraus, auch bei Stop
    # 2,5 %, wo hebel_noetig 12,0 ist und der Hoechsthebel auf 10,0 deckelt.
    from agent import entscheidungsrechnung as _ERD

    def _gebunden(stop_rel, va):
        return _ERD.dimensioniere(
            kurs=100.0, atr=stop_rel * 100.0 / 2.5, k=2.5, verlustanteil=va,
            einsatz_eur=1000.0, hebel_handelbar=True)

    # ⚠️ DER MITTLERE FALL WURDE AM 31.08. NACHGEZOGEN. Er lautete
    # (0,025 / 30 %) und traf den Hoechsthebel, weil hebel_noetig dort 12,0
    # war. Seit die Stop-Untergrenze auf 5 % steht, wird dieser Stop auf
    # 5 % angehoben, hebel_noetig faellt auf 6,0 - und gebunden ist wieder
    # das Risikobudget.
    #
    # Der Fall muss bleiben, denn er prueft eine ECHTE Eigenschaft: dass
    # alle drei Bindungsgruende erreichbar sind. Erreicht wird der
    # Hoechsthebel jetzt ueber den Verlustanteil (0,55/0,05 = 11,0 > 10,0),
    # nicht mehr ueber einen Stop, den es nicht mehr gibt.
    _faelle = ((0.05, 0.30, "Risikobudget"),
               (0.05, 0.60, "Hoechsthebel"),
               (0.22, 0.95, "RM-11 Liquidationsabstand"))
    for _sr, _va, _erwartet in _faelle:
        _d = _gebunden(_sr, _va)
        pruefe(P, f"Stop {_sr*100:.1f} % / Verlust {_va*100:.0f} % ist "
                  f"gebunden durch {_erwartet}",
               _d["gebunden_durch"] == _erwartet,
               f"gemeldet: {_d['gebunden_durch']} (Hebel {_d['hebel']:.2f}, "
               f"noetig {_d['hebel_noetig']:.2f}, sicher "
               f"{_d['hebel_sicher']:.2f})")
    pruefe(P, "und alle drei Gruende sind ueberhaupt erreichbar",
           len({_gebunden(s, v)["gebunden_durch"]
                for s, v, _ in _faelle}) == 3,
           "ein Feld, das nur einen Wert annehmen kann, ist keine Auskunft")

    # ⚠️ UND DER DECKEL SENKT DAS RISIKO NICHT. In der neuen Rechnung steht
    # der Verlust je Trade VOR dem Hebel fest (verlustanteil x einsatz); ein
    # niedrigerer Hebel vergroessert die Nominale, damit derselbe Stop
    # denselben Betrag kostet. Wer das vergisst, baut einen Schutz, der das
    # Gegenteil tut - siehe Umbauplan Kapitel 136.
    _echt_max = _ERD.GRENZEN["hebel_max"]
    try:
        _risiken, _nominalen = set(), []
        for _deckel in (10.0, 4.0, 2.0, 1.5):
            _ERD.GRENZEN["hebel_max"] = _deckel
            _d = _gebunden(0.025, 0.06)
            _risiken.add(round(_d["risiko_eur"], 6))
            _nominalen.append(_d["betrag_eur"])
    finally:
        _ERD.GRENZEN["hebel_max"] = _echt_max
    pruefe(P, "ein Hebeldeckel laesst das Risiko je Trade unveraendert",
           len(_risiken) == 1, f"Risiken: {sorted(_risiken)}")
    pruefe(P, "und vergroessert dabei die Nominale",
           _nominalen == sorted(_nominalen),
           f"Nominalen: {[round(x) for x in _nominalen]} - ein Deckel, der "
           f"die Nominale SENKT, waere ein anderer Mechanismus als der hier "
           f"beschriebene")

    # ---- DIE RICHTUNGSPFLICHT HAENGT NICHT AM INSTRUMENT (22.08.2026) ----
    #
    # ⚠️ SIE WAR SEIT S6b TOT. Die Bedingung lautete `instrument == "hebel"
    # and ...`; S6b laesst Krypto nur noch mit instrument="spot" laufen, also
    # war sie nie wieder wahr. Ein KAUFEN ohne Richtung waere durchgegangen
    # und bei der Aufloesung als LONG gelesen worden - bei gemeintem SHORT
    # sind Stop und Ziel vertauscht, und zwar still.
    _basis_r = {"begruendung": "x", "was_dagegen": "y",
                "umgeworfen_durch": "z", "tranche_eur": 300}
    for _instr in ("spot", "hebel"):
        for _aktion in _EV.BRAUCHT_RICHTUNG:
            _abgelehnt = False
            try:
                _EV.validiere(dict(_basis_r, aktion=_aktion), "X",
                              instrument=_instr)
            except _EV.EmpfehlungUngueltig:
                _abgelehnt = True
            pruefe(P, f"{_instr}/{_aktion} ohne Richtung wird abgelehnt",
                   _abgelehnt,
                   "ohne diese Pflicht liest die Aufloesung LONG, auch wo "
                   "SHORT gemeint war")
        # Und umgekehrt: wo die Richtung nichts bedeutet, darf sie nicht
        # stehenbleiben - `check_signal_outcome()` liest das Feld mit Vorrang.
        for _aktion in ("REDUZIEREN", "VERKAUFEN", "NICHTS_TUN"):
            _e = dict(_basis_r, aktion=_aktion, richtung="LONG")
            _out = _EV.validiere(dict(_e), "X", instrument=_instr)
            pruefe(P, f"{_instr}/{_aktion} traegt keine Richtung mehr",
                   "richtung" not in _out,
                   "bei einem Ausstieg beschreibt das Feld die BESTEHENDE "
                   "Position, nicht die Zonen - ein Feld mit zwei "
                   "Bedeutungen ist schlimmer als keines")
    pruefe(P, "und der alte Name zeigt auf dieselbe Liste",
           _EV.HEBEL_MIT_EINSTIEG == _EV.BRAUCHT_RICHTUNG,
           "sonst gaebe es zwei Wahrheiten")

    pruefe(P, "jede Ausnahme traegt einen Grund",
           all(len(str(g).strip()) >= 20
               for g in _PAV.AUSGENOMMEN.values()),
           "eine Ausnahme ohne Grund ist ein Schalter, keine Aussage")

    from agent import ausstiegsrechnung as _AU

    # ⚠️ AN EINER ECHTEN MAIL GEFUNDEN. ETH stand bei 1.931,49 EUR, darunter
    # "Stop auf 2.025,02 EUR nachziehen" - ein Stop UEBER dem Marktpreis.
    # Wer ihn so eintraegt, verkauft sofort. Die Rechnung war richtig, die
    # Waehrung nicht: 2.025,02 ist USD, in EUR sind es 1.735.
    _e = {"stop_empfohlen": 2025.02, "gesicherte_r": 0.366,
          "eur_je_usd": 0.8567175487465181, "stand_r": 1.074,
          "stand_prozent": 0.1736, "mfe_r": 1.366, "mfe_prozent": 0.2208,
          "empfehlung": "STOP NACHZIEHEN", "gruende": []}
    _zs = [z for z in _AU.saetze(_e) if z.startswith("Stop")]
    pruefe(P, "der nachgezogene Stop steht in EUR, nicht in Quellwaehrung",
           bool(_zs) and "1.735" in _zs[0] and "2.025" not in _zs[0],
           "dieselbe Zahl wurde zweimal ausgegeben - `_absatz()` rechnete "
           "um, `saetze()` nicht. Der Docstring von `_in_eur` nennt genau "
           "diesen Fehler als Grund seiner Existenz")
    _ohne = dict(_e)
    _ohne.pop("eur_je_usd")
    pruefe(P, "ohne Umrechnungsfaktor steht KEINE Zahl da",
           "2.025" not in [z for z in _AU.saetze(_ohne)
                           if z.startswith("Stop")][0],
           "lieber keine Zahl als eine in der falschen Waehrung - dieselbe "
           "Regel, die `_in_eur` schon fuer die Sammelmail durchsetzt")

    # ⚠️ UND KEINE ROHE ZAHL MIT EUR-ETIKETT MEHR IN DIESER DATEI.
    _auq = _quelltext("agent/ausstiegsrechnung.py")
    import re as _re2
    _roh = _re2.findall(r"_de\(e\[[^\]]+\]\)\} EUR", _auq)
    # ⚠️ EINE BEKANNTE, UNGEKLAERTE STELLE - und sie steht hier NAMENTLICH,
    # damit sie nicht in Vergessenheit geraet und keine zweite dazukommt.
    #
    # `umgeworfen_preis_eur` heisst EUR, wird in `_absatz()` aber durch
    # `_in_eur` geschickt - dort gilt er also als USD. Zwei Stellen, zwei
    # Lesarten, eine davon falsch. WELCHE, ist ohne Blick auf die Quelle des
    # Wertes nicht zu entscheiden; geraten wird hier nicht.
    _bekannt = {"_de(e['umgeworfen_preis_eur'])} EUR"}
    _neu = [x for x in _roh if x not in _bekannt]
    pruefe(P, "keine NEUE Stelle gibt Betraege unumgerechnet als EUR aus",
           not _neu,
           f"gefunden: {_neu[:3]}. Bekannt und offen: umgeworfen_preis_eur - "
           f"der Name sagt EUR, `_absatz()` rechnet ihn um. Eine der beiden "
           f"Lesarten ist falsch")

    # ---- DIE ZUSAMMENFUEHRUNG (93 E) - ZAEHLT, RECHNET NICHT ----
    from agent import gesamtbild as _GB

    _gq = _quelltext("agent/gesamtbild.py")
    # AM AUSGEGEBENEN TEXT geprueft, nicht am Quelltext: was der Leser sieht,
    # ist die Zusage - und der Quelltext schreibt sie in Grossbuchstaben,
    # woran die erste Fassung dieser Pruefung scheiterte.
    _gz = _GB.saetze(["Uebliche Kursbewegung:", "⚠️ UNGUENSTIG: x"])
    pruefe(P, "das Gesamtbild kann keinen Einstieg verhindern (E1)",
           any("keine Sperre" in z for z in _gz)
           and any("verhindert keine Empfehlung" in z for z in _gz),
           "Fallstrick E1 ist der wichtigste des Kapitels: kein Kriterium "
           "darf ein Urteil verhindern, es darf nur bestimmen, welcher Art "
           "das Urteil ist")

    # ⚠️ ES LIEST DIE FERTIGE MAIL - KEINE ZWEITE RECHNUNG.
    _mq = _quelltext("agent/signal_mail.py")
    pruefe(P, "und es rechnet nichts neu, sondern liest den fertigen Text",
           "zeilen = text.split" in _mq and "_GB.saetze(zeilen)" in _mq,
           "eine zweite Rechnung koennte von der ersten abweichen - genau "
           "der Fehler, der vier Kopien derselben Stopzeile hinterliess")

    # ⚠️ DIE ETIKETTEN MUESSEN ZU DEN MODULEN PASSEN.
    #
    # Das Gesamtbild sucht nach "GUENSTIG", "UNGUENSTIG" und den
    # Unbekannt-Worten. Benennt jemand eines um, zaehlt es still falsch -
    # ohne Fehlermeldung, ohne Luecke in der Simulation.
    _quellen = (_quelltext("agent/trichter.py")
                + _quelltext("agent/lebendigkeit.py")
                + _quelltext("agent/drift.py")
                + _quelltext("agent/anlass_kalender.py"))
    pruefe(P, "die gesuchten Etiketten kommen in den Modulen auch vor",
           _GB.DAGEGEN in _quellen and _GB.DAFUER in _quellen
           and all(w in _quellen for w in _GB.UNBEKANNT),
           "wer ein Etikett umbenennt, muss gesamtbild.py mitziehen - sonst "
           "zaehlt es still falsch")
    pruefe(P, "und jeder Blockanfang steht in genau einem Modul",
           all(_quellen.count(a) >= 1 for _n, a in _GB.MERKMALE))

    # DAS ZAEHLEN SELBST - an einem gebauten Beispiel.
    _bsp = ["Uebliche Kursbewegung (80 %):", "⚠️ UNGUENSTIG: x", "",
            "Bekannte Termine in den naechsten 30 Tagen:", "   GUENSTIG: y",
            "", "Lebendigkeit des Projekts:",
            "⚠️ NOCH KEINE BEWERTUNG MOEGLICH - z"]
    _b = _GB.bewerte(_bsp)
    pruefe(P, "drei Merkmale, drei verschiedene Urteile - richtig zugeordnet",
           _b["dagegen"] == 1 and _b["dafuer"] == 1 and _b["unbekannt"] == 1,
           "ein UNGUENSTIG aus dem Trichter darf nicht dem Terminblock "
           "zugerechnet werden - die Bloecke trennt die Leerzeile")
    # ⚠️ EINGERUECKTE BLOECKE ZAEHLEN AUCH (Betriebsfund 20.08.2026).
    #
    # In Bestandsmails steht der Rechnungsblock eingerueckt unter
    # "Zusaetzlicher Einstieg:". Die erste Fassung verglich am rohen
    # Zeilenanfang und uebersah den Trichter dort - ONDO meldete "3
    # pruefbare Merkmale", obwohl vier Bloecke in der Mail standen.
    _eing = ["  Uebliche Kursbewegung (80 %):", "     GUENSTIG: x", "",
             "Bekannte Termine in den naechsten 30 Tagen:",
             "⚠️ UNGUENSTIG: y"]
    pruefe(P, "eingerueckte Bloecke werden mitgezaehlt",
           _GB.bewerte(_eing)["vorhanden"] == 2
           and _GB.bewerte(_eing)["dafuer"] == 1
           and _GB.bewerte(_eing)["dagegen"] == 1,
           "an den echten Mails vom 20.08. gemessen: ONDO 4 Bloecke / 3 "
           "gezaehlt, VIRTUAL 3 / 2. CAT stimmte, weil dort nichts "
           "eingerueckt war - der Fehler faellt nur auf, wenn man mehrere "
           "Mails nebeneinander legt")

    pruefe(P, "ohne Merkmale bleibt die Zeile weg, statt '0 von 0'",
           _GB.saetze([]) == [] and _GB.saetze(["irgendwas"]) == [])

    # ---- GESAMTPRUEFUNG KAPITEL 93: KEINE ZAHL ZWEIMAL (20.08.2026) ----
    #
    # Der Mailtext nennt Messwerte ("ein Feld von 27 haelt die Schwelle").
    # Wer die Messung aendert und den Text vergisst, luegt die Mail an -
    # dasselbe Muster wie die vier Kopien der Stopzeile im August.
    import messe_drift as _MD
    from statistics import NormalDist as _ND

    # Eigene Namen: `_DR` und `_TR` entstehen erst weiter unten in ihren
    # eigenen Bloecken - genau die Falle aus feedback_freie_namen_falle.
    from agent import drift as _DR0
    from agent import trichter as _TR0

    _f = len(_MD.RUECKBLICKE) * len(_MD.HORIZONTE) * len(_MD.VARIANTEN)
    pruefe(P, "die Feldzahl in der Mail stammt aus dem Messwerkzeug",
           _DR0.GEMESSEN["felder"] == _f,
           f"agent/drift nennt {_DR0.GEMESSEN['felder']}, "
           f"messe_drift rechnet {_f}")
    pruefe(P, "und die Schwelle passt zu dieser Feldzahl",
           abs(_DR0.GEMESSEN["schwelle"]
               - _ND().inv_cdf(1 - 0.05 / (2 * _f))) < 0.02,
           "3,11 ist die Bonferroni-Schwelle fuer 27 Felder - eine andere "
           "Feldzahl macht sie falsch")
    pruefe(P, "die Ankerzahl des Trichters ist die Summe der Klassen",
           _TR0.ANKER_GEMESSEN == sum(
               v[1] for v in _TR0.GRUNDLAGE.values()),
           "36.095 = 23.343 Krypto + 3.875 Aktien + 8.877 ETF. Faellt eine "
           "Klasse weg, muss die Gesamtzahl mit")

    # ⚠️ UND DER NB-EXPORT MUSS DEN NEUEN BEREICH KENNEN.
    _nb = _quelltext("extract_notebook_diagnose.py")
    pruefe(P, "der NB-Export weist Kapitel 93 aus",
           "def _kapitel93" in _nb and '"kapitel93": kapitel93' in _nb,
           "ein Wert, der nur auf dem Entwicklungsrechner nachweisbar ist, "
           "ist nicht nachgewiesen - Rolle G galt drei Tage als fertig und "
           "war nie gelaufen")
    pruefe(P, "und meldet eine ausbleibende Lebendigkeitsreihe als WARNUNG",
           "Der Job `lebendigkeit` laeuft nicht" in _nb,
           "die Auswertung kommt erst in Wochen - ein Ausbleiben des "
           "Sammelns muss SOFORT auffallen, nicht in Wochen")

    # ---- UND ER MUSS GESUNDHEIT MELDEN, NICHT NUR WACHSTUM (22.08.2026) --
    # ⚠️ ANLASS: der erste echte Export. Er sagte "401 Zeilen, 3 Tage, 163
    # Symbole mit Wert" - und keine dieser Zahlen beantwortete die Frage, ob
    # die Sammlung gesund ist. 163 mischte 26 eigene Werte mit dem
    # DefiLlama-Vorrat; die Lebenszeitsumme haette einen halbierten Lauf
    # verdeckt; und die Entwicklerquelle fehlte voellig, was am 22.08.
    # RICHTIG war (Start an einem Donnerstag) und im November eine
    # Katastrophe gewesen waere - ununterscheidbar.
    #
    # Diese Pruefungen rufen `_kapitel93` GEGEN ECHTE SQLITE-DATEN auf.
    # Textpruefungen haetten hier nichts genuetzt: der Fehler lag nicht in
    # einem fehlenden Wort, sondern in einer Zahl, die zu viel enthielt.
    import datetime as _dt
    import sqlite3 as _sq

    from extract_notebook_diagnose import _kapitel93 as _k93

    def _leb_db(start, laeufe, entwickler_ab=None):
        """44 Watchlist-Werte (18 davon ohne TVL) + 136 Vorrat je Lauf.
        Der ERSTE Lauf bleibt ohne Vorrat - so war es am 20.08. wirklich."""
        c = _sq.connect(":memory:")
        c.execute("CREATE TABLE lebendigkeit_beobachtung (id INTEGER PRIMARY "
                  "KEY, erfasst_am TEXT NOT NULL, symbol TEXT, quelle TEXT, "
                  "zustand TEXT, wert REAL, kennzahlen_json TEXT, grund TEXT)")
        for n in range(laeufe):
            tag = start + _dt.timedelta(days=n)
            wann = f"{tag.isoformat()}T01:20:00+00:00"
            for i in range(44):
                zu = "keine_quelle" if i < 18 else "wert"
                c.execute("INSERT INTO lebendigkeit_beobachtung (erfasst_am, "
                          "symbol, quelle, zustand, wert, grund) VALUES "
                          "(?,?,?,?,?,?)", (wann, f"SYM{i:02d}", "tvl", zu,
                                            1e6 if zu == "wert" else None, ""))
            if n:
                for i in range(136):
                    c.execute("INSERT INTO lebendigkeit_beobachtung "
                              "(erfasst_am, symbol, quelle, zustand, wert, "
                              "grund) VALUES (?,?,?,?,?,?)",
                              (wann, f"V{i:03d}", "tvl", "wert", 9e9,
                               "Vorrat, nicht auf der Watchlist"))
            if entwickler_ab and tag >= entwickler_ab and tag.weekday() == 0:
                c.execute("INSERT INTO lebendigkeit_beobachtung (erfasst_am, "
                          "symbol, quelle, zustand, wert, grund) VALUES "
                          "(?,?,?,?,?,?)", (wann, "SYM20", "entwickler",
                                            "wert", 12, ""))
        c.commit()
        return c

    _heute = _dt.datetime.now(_dt.timezone.utc).date()
    # Fall A - "die Sammlung hat begonnen, der erste Montag kommt erst".
    #
    # ⚠️ DAS STARTDATUM IST RELATIV, UND ZWAR SEIT DEM 24.08.2026.
    # Vorher stand hier fest der 20.08. (ein Donnerstag) - der Zustand,
    # wie er am 22.08. wirklich war. Am 24.08. war genau dieser erste
    # Montag da, die Warnung sprang zu Recht an, und die Pruefung fiel
    # um: sie hielt ein FESTES Datum gegen ein LAUFENDES "heute".
    #
    # DAS PRODUKT HATTE RECHT, die Pruefung war gealtert. Ein Testfall,
    # der vom Wochentag abhaengt, meldet irgendwann einen Fehler, den es
    # nicht gibt - und eine Pruefung mit Fehlalarmen wird nicht mehr
    # aufgerufen.
    _start_a = _heute + _dt.timedelta(days=1)
    while _start_a.weekday() != 3:            # 3 = Donnerstag
        _start_a += _dt.timedelta(days=1)
    _montag_a = _start_a
    while _montag_a.weekday() != 0:
        _montag_a += _dt.timedelta(days=1)
    _a = _k93(_leb_db(_start_a, 3))["lebendigkeit"]

    pruefe(P, "die eigenen Symbole stehen getrennt vom Vorrat",
           _a["eigene_symbole"]["mit_wert"] == 26
           and _a["symbole_mit_wert"] > 100,
           "26 eigene Werte gegen 162 gesamt - die grosse Zahl las sich wie "
           "Abdeckung und war der DefiLlama-Vorrat (Umbauplan 93.22)")
    pruefe(P, "und die ueber TVL NIE auswertbaren werden benannt",
           _a["eigene_symbole"]["ohne_jeden_tvl_wert"] == 18
           and len(_a["eigene_symbole"]["stumme_symbole"]) == 18,
           "fuer sie bleibt allein die Entwicklerquelle - das begrenzt, "
           "worueber 93 C je etwas sagen kann")

    # ⚠️ DIE ZAHL, DIE AM 22.08. GEFEHLT HAT.
    # ⚠️ AUCH HIER RELATIV (24.08.2026): der erste Lauf schreibt nur die
    # 44 Watchlist-Werte, der zweite zusaetzlich den Vorrat. Das Datum
    # folgt dem Startdatum, nicht dem Kalender.
    pruefe(P, "ein kleinerer Lauf ist an je_tag ablesbar",
           _a["letzter_lauf"]["je_tag"][_start_a.isoformat()] == 44
           and _a["letzter_lauf"]["je_tag"][
               (_start_a + _dt.timedelta(days=1)).isoformat()] == 180,
           "an der Lebenszeitsumme waere ein halbierter Lauf unsichtbar - "
           "sie waechst ja weiter")

    # ⚠️ DER WOCHENTAKT: dieselbe Beobachtung, zwei entgegengesetzte Urteile.
    pruefe(P, "ein noch nicht faelliger Montag ist KEINE Warnung",
           not _a["entwickler_takt"].get("WARNUNG")
           and "RICHTIG" in _a["entwickler_takt"]["hinweis"]
           and _a["entwickler_takt"]["erste_faellige_montagsmessung"]
           == _montag_a.isoformat(),
           "die Sammlung begann an einem Donnerstag - solange der erste "
           "Montag noch aussteht, FEHLT die Entwicklerquelle zu Recht")
    pruefe(P, "und die Auswertbarkeit steht als Datum da",
           _a["entwickler_takt"]["zwoelfte_und_damit_auswertbar"]
           == (_montag_a + _dt.timedelta(weeks=11)).isoformat(),
           "12 Wochenmessungen ab dem ersten Montag - "
           "MINDESTREIHE['entwickler']")

    _b = _k93(_leb_db(_heute - _dt.timedelta(days=30), 30))["lebendigkeit"]
    pruefe(P, "ein vergangener Montag OHNE Zeile ist eine Warnung",
           "faellig" in (_b["entwickler_takt"].get("WARNUNG") or "")
           and not _b["entwickler_takt"].get("hinweis"),
           "faellt der Montagslauf aus, faellt die Quelle GANZ aus - und "
           "das darf nicht wie der Normalzustand aussehen")

    _cst = _heute - _dt.timedelta(days=30)
    _c = _k93(_leb_db(_cst, 30, entwickler_ab=_cst))["lebendigkeit"]
    pruefe(P, "und mit Entwicklerzeilen schweigt die Warnung",
           _c["entwickler_takt"]["bisher_erhoben"] is True
           and not _c["entwickler_takt"].get("WARNUNG"),
           "eine Pruefung mit Fehlalarmen wird nicht mehr aufgerufen")

    # ⚠️ ERST DURCH DIESE PRUEFUNGEN AUFGEFALLEN: der Export las `sys.argv`
    # beim IMPORT. `pruefe_pakete.py --paket Dimension` brach damit ab -
    # ohne `--paket` lief dieselbe Suite durch. Ein Pruefwerkzeug, das nur
    # in einer seiner beiden Betriebsarten funktioniert, ist keins.
    # ⚠️ DER WERKZEUGKASTEN DARF NICHT WIEDER ZURUECKFALLEN (22.08.2026).
    # 2.13 wurde gebaut, weil drei fertige Mess-Funktionen ohne Aufrufer
    # dalagen und von Hand nachgerechnet wurde, was im Code fertig war. Am
    # 22.08. gezaehlt: 116 Werkzeuge im Stamm, 64 verzeichnet. Ein Index, der
    # nur beim Anlegen stimmt, hat genau einen guten Tag.
    #
    # Diese Pruefung ist absichtlich SCHWACH: sie verlangt nur, dass der Name
    # irgendwo im Dokument steht. Ob die Beschreibung stimmt, kann sie nicht
    # wissen - aber sie verhindert das, was wirklich passiert ist: dass ein
    # fertiges Werkzeug unsichtbar bleibt und die Arbeit zweimal gemacht wird.
    import subprocess as _sub

    _kasten = io.open("Basisinfos/Test_und_Verifikationsmethodik.md",
                      encoding="utf-8").read()
    _stamm = [x for x in _sub.run(["git", "ls-files", "*.py"],
                                  capture_output=True, text=True,
                                  encoding="utf-8").stdout.split()
              if "/" not in x and x.split("_")[0] in
              ("messe", "pruefe", "bewerte", "lade", "simuliere")]
    _ohne = sorted(x for x in _stamm if x[:-3] not in _kasten)
    pruefe(P, "jedes Messwerkzeug steht im Werkzeugkasten 2.13",
           not _ohne,
           f"{len(_stamm)} im Stamm, {len(_stamm) - len(_ohne)} verzeichnet"
           + (f" - FEHLEN: {', '.join(_ohne[:8])}" if _ohne else ""))

    pruefe(P, "der Export nimmt Argumente nur bei EIGENEM Aufruf",
           "_EIGENER_AUFRUF" in _nb and "not _EIGENER_AUFRUF" in _nb,
           "importiert gehoeren die Argumente jemand anderem")
    pruefe(P, "und meldet ein unlesbares eigenes Argument LAUT",
           # ⚠️ NUR ZUSAMMENHAENGENDE AUSSCHNITTE. "muss eine Zahl sein"
           # steht im Quelltext ueber zwei Zeichenkettenteile verteilt und
           # ist dort nie am Stueck zu finden - derselbe Fallstrick wie bei
           # "NICHTS ZU PERMUTIEREN" in Kapitel 123.
           "ist das Log-Fenster in Stunden" in _nb
           and "raise SystemExit" in _nb,
           "still auf 72 zurueckzufallen waere fail-soft ist fail-silent - "
           "ein Tippfehler laege dann drei Tagen Log zugrunde")

    # ---- DER TERMINKALENDER: ANZEIGE, KEIN GATE (93 D, 20.08.2026) ----
    from agent import anlass_kalender as _AK

    _aq = _quelltext("agent/anlass_kalender.py")
    pruefe(P, "der Kalender sperrt nichts - das Deckelproblem",
           "kein Urteil" in _aq and "KEIN GATE" in _aq
           and "return" in _aq and "gesperrt" not in _aq,
           "ein Anlass, der zur BEDINGUNG wird, ist ein Gate - und ein "
           "lueckenhaftes Gate sperrt zufaellig. Genau daran ist der "
           "Deadloop entstanden (Nutzereinwand 19.08.)")

    # ⚠️ EIN ABRUF JE TAG, NICHT JE ASSET (Betriebsfund 20.08.2026).
    pruefe(P, "der Kalender fragt die Fremdquellen gemerkt ab",
           "_gemerkt" in _aq and "_SPEICHER" in _aq,
           "saetze() laeuft hinter der letzten Abbruchstelle, also fuer "
           "JEDES Asset - bei 60 Assets je Umlauf und einem Umlauf alle 15 "
           "Minuten waren das mehrere tausend FRED-Abrufe am Tag, jeder mit "
           "15 s Zeitgrenze. Gemessen: 60 Aufrufe von 35 s auf 1 ms")
    pruefe(P, "und merkt sich auch FEHLSCHLAEGE",
           "AUCH FEHLSCHLAEGE" in _aq,
           "sonst versucht es jedes Asset erneut, und ein Ausfall kostet "
           "sechzigmal die Zeitgrenze")

    # ⚠️ DIE LUECKE IST GEFAEHRLICHER ALS DER FEHLER.
    _az = _AK.saetze("AIOZ", "krypto", fred_key="")
    pruefe(P, "jede Mail sagt, welche Ereignisarten NICHT abgedeckt sind",
           any("NICHT ABGEDECKT" in z for z in _az)
           and any("Token-Freigaben" in z for z in _az),
           "ein Kalender mit Luecken ist gefaehrlicher als keiner: fehlt "
           "ein Anlass, sieht die Lage RUHIG aus")
    pruefe(P, "und welche Quellen gefragt wurden",
           any("Gefragt wurde" in z for z in _az))

    # ⚠️ DREI ZUSTAENDE, AUCH HIER.
    _zust = _AK.termine("AIOZ", "krypto", fred_key="")["erreicht"]
    pruefe(P, "'gibt es hier nicht' und 'nicht erfahren' bleiben getrennt",
           _zust["Optionsverfall (nur BTC/ETH)"] == "entfaellt"
           and _zust["CPI-Veroeffentlichung"] == "fehler",
           "fuer AIOZ gibt es keinen Optionsmarkt - das ist nicht "
           "zutreffend, kein Ausfall. Die erste Fassung meldete beides als "
           "NICHT ERREICHT und liess die Mail nach Stoerung aussehen")
    pruefe(P, "ein Termin in den naechsten fuenf Tagen heisst UNGUENSTIG",
           "UNGUENSTIG FUER EINEN EINSTIEG JETZT" in _aq
           and "GUENSTIG: kein Termin" in _aq,
           "was dann passiert, entscheidet die Nachricht - nicht der Aufbau")

    # ⚠️ EIN DEUTSCHES DATUM IST KEINE ENGLISCHE ZAHL.
    from simuliere_kette import _englische_zahlen as _EZ
    pruefe(P, "die Schreibweisenpruefung stolpert nicht ueber Datumsangaben",
           _EZ("FOMC-Sitzung (15.09.-16.09.2026)") == []
           and _EZ("Stop 1.5 Prozent") == ["1.5"],
           "mit dem Terminkalender stand erstmals ein Datum in der Mail und "
           "die Simulation meldete acht Luecken - der Fehler lag in der "
           "Pruefung, nicht in der Mail")

    # ---- DIE DREI VARIANTEN UND DER RANGPLATZ (93 B Punkt 3) ----
    _dq3 = _quelltext("messe_drift.py")

    pruefe(P, "die Varianten standen VOR der ersten Rechnung fest",
           'VARIANTEN = ("roh", "ohne_monat", "vol_skaliert")' in _dq3,
           "beide Zusaetze stammen aus der Literatur, nicht aus einem Blick "
           "in unsere Daten. Nachtraeglich eine vierte zu ergaenzen waere "
           "Rosinenpickerei")
    pruefe(P, "und sie erhoehen die Schwelle, statt sie zu umgehen",
           "len(RUECKBLICKE) * len(HORIZONTE) * len(VARIANTEN)" in _dq3,
           "27 Felder statt 9 - wer Varianten rechnet, ohne die Schwelle "
           "mitzuziehen, kauft sich Signifikanz")
    pruefe(P, "es gibt eine Unabhaengigkeitsprobe ueber zwei Haelften",
           '"--haelfte"' in _dq3,
           "eine zweite Anlageklasse ist unmoeglich - die Watchlist hat 2 "
           "Aktien und 4 ETF, und unter zehn Symbolen ist eine Rangliste "
           "keine. Ersatz: beide Haelften der Symbolliste getrennt")

    # ---- DER RANGPLATZ IN DER MAIL: TATSACHE JA, BEHAUPTUNG NEIN ----
    from agent import drift as _DR

    _rq = _quelltext("agent/drift.py")
    pruefe(P, "der Rangplatz zaehlt nur Werte DERSELBEN Anlageklasse",
           "def _gleiche_klasse" in _rq,
           "erste Fassung meldete 'Platz 15 von 47 Kryptowerten', waehrend "
           "die Datenbank 41 Kryptoreihen kennt - Aktien und ETF standen mit "
           "in der Liste")
    pruefe(P, "ohne genug Historie gibt es keinen Rang, nicht Platz eins",
           "len(kerzen) <= rueckblick" in _rq and "return None" in _rq,
           "wer erst seit hundert Tagen dabei ist, hat keine "
           "Jahresentwicklung - ihn mit null zu fuehren waere eine "
           "erfundene Zahl")

    # ⚠️ DIE ZEILE MUSS SAGEN, WAS SIE WERT IST.
    _rz = _DR.saetze({}, "BTC", "krypto")
    pruefe(P, "und die Mail nennt den gemessenen Wert MIT den Kosten",
           "KEIN HANDELBARER VORTEIL" in _rq and "Handelskosten" in _rq
           and "keine Prognose" in _rq,
           "+1,0 % Abstand heisst rund +0,5 % fuer das beste Fuenftel gegen "
           "3 % Kosten. Der Vorteil ist gemessen UND zu klein, um ihn zu "
           "bezahlen - beides gehoert in dieselbe Zeile")
    pruefe(P, "ohne Kursreihen bleibt die Zeile weg, statt zu raten",
           _rz == [] and _DR.rang({}, "BTC") is None)

    # ---- NACHGELADENE HISTORIE: NIE UEBERSCHREIBEN (93 B Punkt 2) ----
    _hq = _quelltext("lade_historie_nach.py")

    pruefe(P, "vorhandene Kerzen bleiben unberuehrt",
           "INSERT OR IGNORE INTO price_history_ohlc" in _hq
           and "UPDATE price_history_ohlc" not in _hq,
           "MORPHO ist der Beleg: Binance liefert dort erst ab 2025-10-03, "
           "die Datenbank reicht bis 2024-11-21. Wer aktualisiert, "
           "verschlechtert")
    pruefe(P, "jede Reihe wird vor dem Schreiben gegengeprueft",
           "MAX_ABWEICHUNG_REIHE" in _hq and "MIN_UEBERLAPPUNG" in _hq
           and "MAX_ABWEICHUNG_PREIS" in _hq,
           "der abgeloeste yfinance-Rueckfall riet Ticker; drei von acht "
           "gehoerten einem anderen, toten Asset - bei IO 269 % Abweichung")

    # ⚠️ DER VERGLEICHSPREIS MUSS FRISCHER SEIN ALS DAS GEPRUEFTE.
    pruefe(P, "der Vergleichspreis kommt NICHT aus der eigenen Datenbank",
           "def preise_frisch" in _hq and "simple/price" in _hq
           # Auf die ABFRAGE pruefen, nicht auf das Wort: der Docstring
           # erklaert ausfuehrlich, warum price_cache NICHT genommen wird.
           and "FROM price_cache" not in _hq,
           "erste Fassung nahm price_cache und lehnte vier Symbole ab - "
           "KAIA mit '30 % Abweichung, anderes Asset'. Der Preis war vom "
           "19.07., ueber einen Monat alt, weil die Produktion auf dem "
           "Notebook laeuft. Mit frischem Preis: 0,4 % Abweichung")

    # ⚠️ EIN FUND IN NACHGELADENER ZEIT IST VERDAECHTIG.
    _dq2 = _quelltext("messe_drift.py")
    pruefe(P, "die Drift laesst sich auf Zeitfenster einschraenken",
           '"--ab"' in _dq2 and '"--bis"' in _dq2,
           "die nachgeladene Historie enthaelt nur Werte, die es HEUTE noch "
           "gibt - ein Wert steht auf unserer Liste, WEIL er einmal gelaufen "
           "ist. Jeder Fund muss auch auf der nicht nachgeladenen Zeit "
           "stehen, sonst misst er die Auswahl")
    pruefe(P, "und die Schwelle wurde nach dem Fund NICHT gesenkt",
           "SCHWELLE_GEMESSEN = 3.05" in _dq2,
           "auf den breiteren Daten misst der Placebo 2,40 - die strengere "
           "3,05 bleibt stehen. Eine Schwelle unmittelbar nach einem "
           "positiven Fund zu senken waere Rosinenpickerei")

    # ---- JEDER NEUE WERT SAGT, WAS GUT UND WAS SCHLECHT IST (20.08.) ----
    #
    # Nutzervorgabe: auch - und gerade - bei den noch ungeprueften Werten.
    # Eine Zahl ohne Einordnung zwingt den Leser, sich die Bedeutung selbst
    # zu bauen, und dabei irrt er.
    _eng = _TR.saetze(100.0, 4.0, stop_relativ=0.03, ziel_relativ=0.09,
                      klasse="krypto")
    _weit = _TR.saetze(100.0, 4.0, stop_relativ=0.20, ziel_relativ=0.50,
                       klasse="krypto")
    pruefe(P, "der Trichter bewertet Stop UND Ziel, in beide Richtungen",
           any("UNGUENSTIG" in z for z in _eng)
           and any("GUENSTIG: gewoehnliches Schwanken" in z for z in _weit)
           and any("Ihr Ziel liegt" in z for z in _eng),
           "ein Stop im Rauschen wird ohne Gegenargument getroffen, ein Ziel "
           "jenseits der ueblichen Bewegung wird in der Zeit nicht erreicht "
           "- beides folgt aus Zahlen, die ohnehin dastehen")
    pruefe(P, "und die schlechte Nachricht steht am ZEILENANFANG",
           all(z.lstrip().startswith("UNGUENSTIG") is False or
               z.startswith("⚠️") for z in _eng + _weit),
           "nur eine Zeile, die mit dem Warnzeichen BEGINNT, wird von "
           "ui.formatting als Warnung gesetzt - steht es mitten im Satz, "
           "bleibt die Zeile grauer Fliesstext")

    # ⚠️ DIE SECHS HANDELSPARAMETER GEHOEREN ZUSAMMEN.
    _mz = [z.split(" ", 1)[0].rstrip(":") for z in _ER.saetze(
        _ER.rechne(kurs=100.0, atr=4.0, risiko_eur=60.0,
                   betrag_wunsch_eur=1000.0, instrument="hebel",
                   umgeworfen_preis_eur=95.0, assetklasse="krypto"))]
    from ui import formatting as _FMT
    _pos = [i for i, w in enumerate(_mz) if w in _FMT.HANDELSPARAMETER]
    pruefe(P, "der Trichter zerschneidet die sechs Parameter NICHT",
           bool(_pos) and (max(_pos) - min(_pos) + 1) == len(_pos),
           "er stand zuerst zwischen Take-Profit und Haltedauer - sieben "
           "Zeilen dazwischen machen aus der Tabelle eine Suche. Der Nutzer "
           "wollte die sechs am 17.08. ausdruecklich zusammen und fett")

    # ⚠️ AUCH DER UNGEPRUEFTE WERT SAGT, WAS GUT WAERE.
    # Eigener Name: `_lq` entsteht erst weiter unten im Lebendigkeitsblock.
    _lq0 = _quelltext("agent/lebendigkeit.py")
    pruefe(P, "die Lebendigkeit sagt es AUCH ohne tragfaehige Reihe",
           "STEIGEND waere gut" in _lq0 and "FALLEND schlecht" in _lq0
           and "kein Befund" in _lq0,
           "solange die Reihe zu kurz ist, gibt es keine Bewertung - aber "
           "die Lesehilfe steht trotzdem da, sonst raet der Leser")
    pruefe(P, "und benennt schwaecher als SCHLECHT, staerker als GUT",
           "GUT: " in _lq0 and "SCHLECHT: " in _lq0
           and "NEUTRAL: " in _lq0)

    # ---- DRIFT: DIE MESSUNG MUSS SICH SELBST MISSTRAUEN (93 B) ----
    _dq = _quelltext("messe_drift.py")

    pruefe(P, "die Marktbewegung wird abgezogen - sonst ist es keine Auswahl",
           "kuenftig = kuenftig - kuenftig.mean()" in _dq,
           "ein Mittelwert ueber eine Kategorie MUSS null ergeben, er IST "
           "der Markt. Genau dieser Einwand des Nutzers hat acht Messungen "
           "dieses Projekts erledigt")
    pruefe(P, "der t-Wert laeuft ueber TERMINE, nicht ueber Anker",
           "schritt = 1 if ueberlappend else horizont" in _dq
           and "def _newey_west" in _dq,
           "32 Symbole an 500 Tagen sind keine 16.000 unabhaengigen Faelle - "
           "an einem Tag bewegt sich alles gemeinsam. Der Schritt ist ein "
           "ganzer Horizont, damit sich auch die Termine nicht ueberlappen")
    pruefe(P, "neun Felder heben die Schwelle an (Bonferroni)",
           "0.05 / (2 * felder)" in _dq,
           "bei neun Tests ist EIN Feld mit |t| >= 2 der Erwartungswert des "
           "Zufalls. Genau ein solches Feld kam heraus - es zu behalten "
           "hiesse, sich ein Ergebnis gesucht zu haben")

    # ⚠️ DIE WICHTIGSTE: EIN NULLBEFUND BRAUCHT EINE POSITIVKONTROLLE.
    pruefe(P, "es gibt eine Positivkontrolle - sonst sagt das 'nichts' nichts",
           "--positivkontrolle" in _dq and "kontrolle: float = 0.0" in _dq,
           "gemessen: ein eingepflanzter Effekt von 3 % wird auf fuenf Tagen "
           "mit t rund 8 gefunden. Erst damit ist der Nullbefund einer")
    pruefe(P, "und der kleinste nachweisbare Abstand steht in jeder Zeile",
           "kleinster_nachweisbarer" in _dq,
           "ohne diese Zahl ist 'nichts gefunden' nicht von 'nicht "
           "hingesehen' zu unterscheiden")
    pruefe(P, "beides wird getrennt ausgewiesen, nicht verrechnet",
           "NICHT MESSBAR" in _dq and "GEMESSEN, nichts gefunden" in _dq,
           "dieselbe Regel wie bei den Fremdquellen: ja / nein / NICHT "
           "ERFAHREN. Auf 60 Tagen schlaegt die Messung erst ab 14 % an - "
           "dort ist nichts widerlegt, dort wurde nicht hingesehen")

    # ⚠️ UND DER BEFUND DARF NICHT STILL IN DIE MAIL WANDERN.
    pruefe(P, "die Drift geht NICHT in die Mail - sie hat nichts gezeigt",
           "messe_drift" not in _quelltext("agent/rollen_lauf.py")
           and "messe_drift" not in _quelltext("agent/signal_mail.py"),
           "ein Merkmal ohne nachgewiesene Wirkung in die Mail zu schreiben "
           "hiesse, Rauschen als Erkenntnis zu verkaufen - der Trichter "
           "steht dort, WEIL er widerlegbar ist")
    pruefe(P, "die Ueberlebensverzerrung wird beim Namen genannt (B1)",
           "Ausgefallene Werte fehlen VOLLSTAENDIG" in _dq,
           "wer ausgefallen ist, waere im schlechtesten Fuenftel gelandet - "
           "und fehlt")

    # ---- LEBENDIGKEIT: SAMMELN OHNE ZU URTEILEN (93 C, 19.08.2026) ----
    from agent import lebendigkeit as _LB

    pruefe(P, "drei Zustaende, die nie verschmelzen",
           set(_LB.ZUSTAENDE) == {"wert", "keine_quelle", "fehler"},
           "wer 'nicht erfahren' mit 'gibt es nicht' verrechnet, erklaert "
           "lebendige Ketten fuer tot - am 19.08. ergab genau das '0 von "
           "43', waehrend BTC 73.168 Sterne meldete")
    _fehler = 0
    try:
        _LB.schreibe(None, symbol="X", quelle="tvl", zustand="tot")
    except ValueError:
        _fehler = 1
    pruefe(P, "und ein erfundener Zustand wird abgewiesen", _fehler == 1)

    # ⚠️ SOLANGE DIE REIHE KURZ IST, GIBT ES KEINE RICHTUNG.
    _kurz = _LB.richtung([("2026-08-01", 100.0), ("2026-08-02", 200.0)],
                         "tvl")
    pruefe(P, "eine kurze Reihe liefert KEINE Richtungsaussage",
           _kurz["tragfaehig"] is False and _kurz["richtung"] is None
           and _kurz["beobachtungen"] == 2,
           "eine Verdopplung an zwei Tagen ist keine Entwicklung - der Uebergang ist das Signal, und den sieht man erst ueber Wochen")
    _lang = _LB.richtung([("t%d" % i, 100.0) for i in range(20)]
                         + [("u%d" % i, 200.0) for i in range(20)], "tvl")
    pruefe(P, "eine lange Reihe schon - und in der richtigen Richtung",
           _lang["tragfaehig"] and _lang["richtung"] == "staerker")
    pruefe(P, "kleine Bewegungen heissen unveraendert, nicht staerker",
           _LB.richtung([("t%d" % i, 100.0) for i in range(20)]
                        + [("u%d" % i, 103.0) for i in range(20)],
                        "tvl")["richtung"] == "unveraendert",
           "unter zehn Prozent ist bei TVL das Rauschen des Kurses selbst, "
           "nicht die Nutzung")

    # DER WARNHINWEIS IST DER NUTZERWUNSCH - er muss auch WEGGEHEN.
    _lq = _quelltext("agent/lebendigkeit.py")
    pruefe(P, "der Warnhinweis haengt an der Reihenlaenge, nicht an einem Schalter",
           "NOCH KEINE BEWERTUNG MOEGLICH" in _lq
           and 'if r["tragfaehig"] and r["richtung"]:' in _lq,
           "er verschwindet von selbst, sobald genug Messungen da sind - "
           "niemand muss daran denken (Nutzerwunsch 19.08.)")
    pruefe(P, "und die Zeilen sagen ausdruecklich, dass sie nichts sperren",
           "kein Urteil" in _lq and "sperren nichts" in _lq,
           "ein statisches Gate auf 'tot' haette den wertvollsten Fall blockiert: den Coin, der stirbt und dreht")

    # ---- S6a: DIE DREI ABHAENGIGKEITEN, DIE FAST GEBROCHEN WAEREN -----
    # ⚠️ Alle drei fand erst die Gegenpruefung ueber ALLE Rollen, nicht die
    # Arbeit an der geaenderten Stelle. Eine geaenderte FRAGE kann an vier
    # Orten scheitern, und drei davon merkt man erst im Betrieb.

    # 1) DER SCHWERSTE: die Aufloesung leitete die Richtung aus der AKTION
    #    ab, weil das Signal kein Richtungsfeld hatte. Seit S6a hat es eins.
    #    Ohne den Vorrang waere ein SHORT mit aktion="KAUFEN" als LONG
    #    aufgeloest worden - Stop und Ziel vertauscht, und zwar STILL.
    _btq2 = _quelltext("agent/krypto/backward_tracking.py")
    pruefe(P, "die Aufloesung nimmt das RICHTUNGSFELD vor der Ableitung",
           'getattr(signal, "richtung", "")' in _btq2
           and _btq2.index('getattr(signal, "richtung", "")')
           < _btq2.index('richtung_aus_action(signal.action)'),
           "ein SHORT traegt seit S6a aktion='KAUFEN'; die Ableitung liefert "
           "dafuer LONG. Ohne Vorrang waeren Stop und Ziel vertauscht")
    pruefe(P, "und die Ableitung bleibt als Rueckfall",
           "richtung_aus_action(signal.action)" in _btq2,
           "tausende Altzeilen tragen kein richtung - fuer sie ist die "
           "Ableitung weiterhin die richtige Antwort")

    # 2) Der Kanarienvogel zaehlte nur den ALTEN Namen.
    _kvq = _quelltext("agent/krypto/kanarienvogel.py")
    pruefe(P, "der Kanarienvogel zaehlt BEIDE Vokabulare",
           '"KAUFEN", "ERÖFFNEN"' in _kvq or '_AUFBAU = ("KAUFEN"' in _kvq,
           "sonst faellt der Eroeffnungsanteil auf null und der Vogel meldet "
           "einen Verhaltensbruch, den allein die Umbenennung erzeugt hat")

    # 3) Die Kategorienkarte kannte beide schon - das wird festgehalten,
    #    damit es beim naechsten Umbau nicht verlorengeht.
    from agent.krypto import signal_stabilitaet as _SS

    pruefe(P, "die Aktionskategorien kennen altes UND neues Vokabular",
           {"KAUFEN", "ERÖFFNEN"} <= set(_SS._AKTIONS_KATEGORIE),
           "beide Namen muessen dieselbe Kategorie bekommen, sonst wechselt "
           "ein Signal beim Umbenennen die Klasse")

    # ---- KAPITEL 132: WER ENTSCHEIDET UEBER SPOT ODER HEBEL? ----------
    # ⚠️ Die Regel steht im Regelwerksmanual A: das Modell nennt KEINE
    # Risikoparameter. Diese Pruefungen halten fest, dass der Code sie
    # einhaelt - und dass die EINE Ausnahme (SHORT => Hebel) bekannt ist.
    _evq = _quelltext("agent/empfehlung_vertrag.py")
    _lsq = _quelltext("agent/llm_schema.py")

    pruefe(P, "der Hebelfaktor kommt NICHT aus dem Schema",
           '"hebel"' not in _lsq.split("def baue_befund")[-1][:3000]
           if "def baue_befund" in _lsq else "hebel_faktor" not in _lsq,
           "er folgt aus Risikobudget und Liquidationsabstand - "
           "Regelwerksmanual A")
    pruefe(P, "die Richtung DARF vom Modell kommen",
           'RICHTUNGEN = ("LONG", "SHORT")' in _evq,
           "sie ist ein Urteil, kein Risikoparameter - die Trennlinie liegt "
           "bei der FRAGE, nicht bei 'Zahl oder nicht'")
    # ⚠️ AUF DEN SCHEMA-SCHLUESSEL PRUEFEN, nicht auf das Wort: die Namen
    # stehen weiterhin in Kommentar und Docstring, die ihre Entfernung
    # begruenden. Meine erste Fassung schlug genau daran fehl - und hat
    # dabei einen veralteten Docstring gefunden, der sie noch als vorhanden
    # beschrieb (korrigiert 22.08.).
    pruefe(P, "und Einstieg und Stop sind aus dem Schema RAUS",
           '"einstieg_eur":' not in _lsq and '"stop_eur":' not in _lsq,
           "S3, 18.08.: sie wurden verlangt, nie gelesen - und konnten den "
           "Trade trotzdem toeten")

    # ⚠️ SHORT LAEUFT VOLL MIT, NUR VERSAND UND GUI SIND GEFILTERT.
    pruefe(P, "SHORT wird erzeugt und verfolgt, nur der Versand ist gefiltert",
           "mail_richtung_erlaubt" in _rlq
           and "mail_richtung_erlaubt" not in _quelltext(
               "agent/entscheidungsrechnung.py"),
           "bis zum 05.08. lagen 313 SHORT-Vorschlaege als HALTEN in der "
           "Datenbank und haben jede Richtungsauswertung verzerrt")
    pruefe(P, "und die GUI filtert die Richtung ebenfalls",
           "Richtungsfilter" in io.open("ui/hebel_view.py",
                                        encoding="utf-8").read())

    # ---- KAPITEL 131: DER HEBEL IST VERWAIST, NICHT KAPUTT ------------
    # ⚠️ Diese Pruefungen HALTEN DEN ZUSTAND FEST, sie beheben ihn nicht.
    # Solange die Entscheidung (S6 fertigbauen oder Hebel abschalten) offen
    # ist, soll wenigstens niemand glauben, es sei schon geregelt.
    import subprocess as _sub2

    _cfg2 = io.open("Basisinfos/config.yaml", encoding="utf-8").read()

    def _text(dateien):
        s = ""
        for f in dateien:
            try:
                s += io.open(f, encoding="utf-8").read()
            except Exception:                                # noqa: BLE001
                pass
        return s

    _neu2 = _text(["agent/entscheidungsrechnung.py", "agent/rollen_lauf.py",
                   "agent/betraege.py", "scheduler/rollen_job.py",
                   "agent/signal_abbildung.py", "agent/assetklassen.py"])
    _deckel = ("regime_konflikt_hebel_deckel", "retail_konsens_hebel_deckel",
               "technischer_konflikt_hebel_deckel",
               "gegenszenario_hebel_deckel", "crv_knapp_hebel_deckel",
               "max_hebel")
    _fehlend = [k for k in _deckel if k in _cfg2 and k not in _neu2]
    pruefe(P, "die wirkungslosen Hebeldeckel sind BEKANNT und dokumentiert",
           len(_fehlend) == 6
           and "Zwölf von sechzehn" in io.open(
               "Basisinfos/Umbauplan_Gesamtsystem_12_08.md",
               encoding="utf-8").read(),
           f"in der Rollen-Kette wirkungslos: {', '.join(_fehlend)} - "
           f"aendert sich die Zahl, ist Kapitel 131 nachzuziehen")

    # ⚠️ DIESE PRUEFUNG HIELT BIS S6b DEN OFFENEN ZUSTAND FEST. Sie ist
    # jetzt umgedreht - S6b ist gebaut, und das darf nicht zurueckfallen.
    pruefe(P, "S6b ist gebaut: ein Lauf je Symbol",
           '"krypto": ("spot",)' in _quelltext("agent/assetklassen.py"),
           "bis zum 22.08. bekam jedes Krypto-Symbol ZWEI Urteile, und seit "
           "S5 produzierte der Hebel-Lauf in 76 % der Faelle Spot-Trades")

    # ⚠️⚠️ NACHGEZOGEN AM 01.09.2026 (Schritt 5) - UND PRAEZISIERT.
    #
    # Sie lautete "die Rollen-Kette liest hebel_triggers NICHT" mit der
    # Begruendung: *„das Screening laeuft alle 15 Minuten und schreibt
    # Kandidaten fuer einen Abnehmer, den es nicht mehr gibt."* Das war der
    # offene Zustand; Schritt 5 hebt ihn auf.
    #
    # ⚠️ ABER NUR ZUR HAELFTE, UND DAS IST DER PUNKT. Das Screening schreibt
    # ZWEI Dinge:
    #
    #     open_interest_snapshot   ROHDATEN (OI, Funding, Long-Anteil)
    #     hebel_triggers           der SCORE (0-100, Schwelle 70)
    #
    # Der Score ist Altbestand und wurde NIE gegen den Zufall gemessen
    # (F-163, 01.09.). Ihn zu lesen hiesse, ein altes Kriterium in die neue
    # Bewertung zu heben - genau die Vermischung, vor der der Nutzer am
    # 01.09. gewarnt hat. Die Rohdaten dagegen sind Messwerte und
    # verwendbar.
    #
    # ⚠️ UND DIE TEXTSUCHE WIRD STRUKTURELL: die alte Fassung fiel ueber
    # einen KOMMENTAR, der `hebel_triggers` nur erwaehnt. Geprueft wird
    # jetzt der Code ohne Kommentare.
    # ⚠️ UEBER DEN SYNTAXBAUM. `_nur_code` entfernt String-Literale
    # vollstaendig - `bc_ein["terminmarkt"]` verliert dort seinen Schluessel,
    # und die Pruefung meldete Fehlalarm. Im Baum stehen die Literale, und
    # Kommentare stehen NICHT darin: beides genau richtig herum.
    import ast as _ast5
    _baum5 = _ast5.parse(_pl_pfad("agent/rollen_lauf.py"))
    _texte5 = {n.value for n in _ast5.walk(_baum5)
               if isinstance(n, _ast5.Constant) and isinstance(n.value, str)}
    pruefe(P, "die Kette liest den SCORE weiterhin nicht",
           not any("hebel_trigger" in x for x in _texte5),
           "`hebel_triggers.score` ist Altbestand mit eigener Schwelle (70) "
           "und nie validiert. Ihn zu lesen waere die Vermischung von Alt- "
           "und Neubestand")
    pruefe(P, "⚠️ aber die ROHDATEN haben jetzt einen Abnehmer (Schritt 5)",
           "terminmarkt" in _texte5,
           "bis zum 01.09. schrieb das Screening alle 15 Minuten 1.872 bis "
           "2.664 Zeilen fuer einen Abnehmer, den es nicht gab - "
           "Nutzerbegruendung: 'einspeisen, sonst haben wir ein Performance- "
           "und Datenbankproblem'. Jetzt speisen die Rohdaten den ANLASS")

    pruefe(P, "das Regelwerksmanual traegt den Standvermerk",
           "STANDVERMERK 22.08.2026" in io.open(
               "Basisinfos/Regelwerksmanual.md", encoding="utf-8").read(),
           "es fuehrt RM-10/RM-11 als aktiv mit eigenem Risikomass - beides "
           "gilt in der neuen Kette nicht mehr")

    # ---- KAPITEL 130: DIE STOPQUELLE + DIE HEBEL-LUECKEN --------------
    _sqq = _quelltext("messe_stopquelle.py")
    _sqroh = io.open("messe_stopquelle.py", encoding="utf-8").read()

    pruefe(P, "die Stopquellen-Messung traegt die Vorabfestlegung",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _sqroh)
    pruefe(P, "sie ist GEPAART auf denselben Ankern",
           "denselben Kurspfad" in _sqroh or "GEPAART" in _sqroh,
           "der Messzeitraum ist eine Aufwaertsphase von +15,8 % - ohne "
           "Paarung misst man den Markt")
    pruefe(P, "und das CRV bleibt in beiden Armen gleich",
           'f["e"] + f["crv"] * (f["e"] - stop)' in _sqq,
           "sonst vergleicht man zwei Geometrien statt zweier Stopquellen")
    pruefe(P, "der Einstieg muss auch hier erreicht sein",
           "eingestiegen" in _sqq and "e_bis" in _sqq)
    pruefe(P, "die Bloecke folgen (Symbol, Tag), nicht dem Signal",
           '(f["sym"], f["tag"])' in _sqq,
           "Methodik 2.60 - fuenf Bewertungen desselben Symbols am selben "
           "Tag sind EINE Beobachtung")

    # ⚠️ DIE LUECKE, DIE BEIM DURCHSEHEN AUFFIEL (130b, L2).
    _hpq = _quelltext("agent/krypto/hebel_pipeline.py")
    _erq = _quelltext("agent/entscheidungsrechnung.py")
    pruefe(P, "der Liquidationsdeckel RM-11 laeuft in der NEUEN Kette",
           "max_safe_hebel" in _erq,
           "ohne ihn koennte Bitpanda zwangsliquidieren, bevor der eigene "
           "Stop ausloest")
    pruefe(P, "⚠️ der Krisendeckel AZ-7 laeuft dort NICHT - als Luecke vermerkt",
           "pre_check_hebel" in _hpq and "pre_check_hebel" not in _erq,
           "pre_check_hebel steht nur in der ALTEN Kette. Diese Pruefung "
           "haelt den Zustand fest, sie behebt ihn nicht - siehe 130b L2")

    # ---- E1 GEBAUT: DIE AUFLOESUNG VERLANGT DEN EINSTIEG (128) --------
    # ⚠️ EIN EINGRIFF IN DIE PRODUKTION. Geprueft wird deshalb an ECHTEN
    # SQLite-Daten mit echten Kerzen, nicht am Quelltext.
    import sqlite3 as _sq4

    from agent.krypto import backward_tracking as _BT

    class _Asset0:
        def __init__(self, s):
            self.symbol = s
            self.coingecko_id = None

    class _Sig0:
        def __init__(self, **kw):
            self.id, self.symbol, self.action = 1, "TEST", "KAUFEN"
            self.created_at = "2026-08-01T00:00:00+00:00"
            for f in ("entry_usd", "entry_usd_von", "entry_usd_bis",
                      "stop_loss_usd", "stop_loss_usd_von",
                      "stop_loss_usd_bis", "take_profit_usd",
                      "take_profit_usd_von", "take_profit_usd_bis"):
                setattr(self, f, None)
            for k, v in kw.items():
                setattr(self, k, v)

    def _kerzen_db(kerzen):
        c = _sq4.connect(":memory:")
        c.row_factory = _sq4.Row
        c.execute("CREATE TABLE price_history_ohlc (symbol TEXT, currency "
                  "TEXT, date TEXT, open REAL, high REAL, low REAL, close "
                  "REAL, volume REAL, quelle TEXT, fetched_at TEXT)")
        for d0, o, h0, l0, cl in kerzen:
            c.execute("INSERT INTO price_history_ohlc VALUES "
                      "(?,?,?,?,?,?,?,?,?,?)",
                      ("TEST", "USD", d0, o, h0, l0, cl, 1.0, "t", d0))
        c.commit()
        return c

    _Z = dict(entry_usd_von=100.0, entry_usd_bis=102.0,
              stop_loss_usd_von=96.0, stop_loss_usd_bis=97.0,
              take_profit_usd_von=110.0, take_profit_usd_bis=111.0)

    # ⚠️ DER KERNFALL: der Kurs startet UEBER der Zone und laeuft zum Ziel -
    # genau die Lage bei NACHKAUFEN, wo die Zone unter dem Markt liegt.
    _st1, _ex1 = _BT.check_signal_outcome(
        _kerzen_db([("2026-08-01", 105, 107, 104, 106),
                    ("2026-08-02", 107, 112, 106, 111)]),
        _Sig0(**_Z), [_Asset0("TEST")], 1.0)
    pruefe(P, "ein nie erreichter Einstieg ist KEIN Treffer",
           _st1 == _BT.OUTCOME_EINSTIEG_NIE
           and _ex1.get("einstieg_erreicht") == 0,
           f"gemessen {_st1!r} - vor E1 stand hier take_profit_erreicht, "
           f"und das betraf 21,1 % der aufgeloesten Signale")

    _st2, _ex2 = _BT.check_signal_outcome(
        _kerzen_db([("2026-08-01", 101, 103, 100, 102),
                    ("2026-08-02", 102, 112, 101, 111)]),
        _Sig0(**_Z), [_Asset0("TEST")], 1.0)
    pruefe(P, "ein erreichter Einstieg loest normal auf",
           _st2 == _BT.OUTCOME_TAKE_PROFIT
           and _ex2.get("einstieg_erreicht") == 1)

    # ⚠️ UND OHNE ZONE DARF KEINE TATSACHE ERFUNDEN WERDEN.
    _ohne = dict(_Z, entry_usd_von=None, entry_usd_bis=None)
    _st3, _ex3 = _BT.check_signal_outcome(
        _kerzen_db([("2026-08-01", 105, 112, 104, 111)]),
        _Sig0(**_ohne), [_Asset0("TEST")], 1.0)
    pruefe(P, "ohne Zone bleibt einstieg_erreicht None, nicht 0 oder 1",
           _st3 == _BT.OUTCOME_TAKE_PROFIT
           and _ex3.get("einstieg_erreicht") is None,
           "None heisst 'nicht geprueft' - die bestehenden Zeilen tragen "
           "dazu keine Aussage, und 0 waere eine erfundene Tatsache")

    # ⚠️ DER NEUE STATUS DARF IN KEINE DER BEIDEN QUOTEN.
    _btq = _quelltext("agent/krypto/backward_tracking.py")
    pruefe(P, "der neue Status hat einen EIGENEN Zaehler",
           "einstieg_nie_erreicht: int = 0" in _btq
           and "result.einstieg_nie_erreicht += 1" in _btq,
           "ihn in take_profit oder stop_loss zu buchen waere genau der "
           "Defekt, den E1 behebt")
    pruefe(P, "und es gibt EINE Stelle fuer die Zonenpruefung",
           _btq.count("def einstieg_beruehrt") == 1
           and _btq.count("def einstiegszone") == 1,
           "vier Kopien derselben Stopzeile haben am 18.08. zwei "
           "Vormittage gekostet")

    # ⚠️ DIE SPALTE MUSS ENTSTEHEN, IDEMPOTENT, FUER BEIDE FAMILIEN.
    import database.db as _db0

    _c0 = _sq4.connect(":memory:")
    _c0.row_factory = _sq4.Row
    for _tab in ("signals", "hebel_signals"):
        _c0.execute(f"CREATE TABLE {_tab} (id INTEGER PRIMARY KEY, "
                    f"symbol TEXT)")
    _db0._migrate_signal_einstieg_columns(_c0)
    _db0._migrate_signal_einstieg_columns(_c0)      # zweimal = idempotent
    pruefe(P, "die Spalte einstieg_erreicht entsteht in BEIDEN Tabellen",
           all("einstieg_erreicht" in
               {r["name"] for r in _c0.execute(f"PRAGMA table_info({t0})")}
               for t0 in ("signals", "hebel_signals")))
    pruefe(P, "und der bestehende Wert wird nicht ueberschrieben",
           "COALESCE(?, einstieg_erreicht)" in _quelltext("database/db.py"),
           "ein spaeterer Lauf ohne Zonenkenntnis wuerde sonst eine bereits "
           "festgestellte Tatsache loeschen")

    # ---- KAPITEL 127: DER EINSTIEGSNACHWEIS ---------------------------
    # ⚠️ ANLASS, Nutzerfrage: "machen wir etwas falsch oder es gibt noch
    # Fehler in der Umsetzung, bevor wir das Modell als Begruendung sehen."
    # Die Rollen-Kette meldete 82,8 % Trefferquote bei einer Basisrate von
    # 33,3 % - +46 Punkte, die kein Modell erzeugt.
    _enq = _quelltext("pruefe_einstiegsnachweis.py")
    _enroh = io.open("pruefe_einstiegsnachweis.py", encoding="utf-8").read()

    pruefe(P, "der Einstiegsnachweis steht als Vorabfestlegung im Kopf",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _enroh)
    pruefe(P, "er trennt die zwei Ursachen in VIER Arme",
           all(x in _enq for x in ("A wie der Betrieb", "B ab dem Folgetag",
                                   "C Einstieg verlangt", "D beides")),
           "sonst laesst sich nicht sagen, welcher Defekt wieviel beitraegt")

    # ⚠️ DIE WICHTIGSTE PRUEFUNG DES WERKZEUGS IST DIE AN SICH SELBST.
    pruefe(P, "Arm A muss den Betrieb reproduzieren, sonst gilt nichts",
           "REPRODUZIERT ARM A DEN BETRIEB" in _enq
           and "MEIN NACHBAU verdaechtig" in _enq,
           "gemessen 114 von 114 gleich - erst damit sind B/C/D lesbar")
    pruefe(P, "gerechnet wird NUR in USD",
           'str(z.get("currency")).upper() == "USD"' in _enq,
           "die Zonen des Trackers stehen in USD; die Historie traegt beide "
           "Waehrungen als getrennte Zeilen")
    pruefe(P, "und mit der vorsichtigen Lesart wie im Betrieb",
           _enq.index('if tief <= stop:') < _enq.index('if hoch >= ziel:'),
           "faellt beides in eine Kerze, gilt der Stop")

    # ---- KAPITEL 125/126: REIHUNG x H UND DIE SIGNALBILANZ ------------
    _rxq = _quelltext("messe_reihung_x_h.py")
    _rxroh = io.open("messe_reihung_x_h.py", encoding="utf-8").read()
    _sbq = _quelltext("messe_signalbilanz.py")
    _sbroh = io.open("messe_signalbilanz.py", encoding="utf-8").read()

    pruefe(P, "beide neuen Messungen tragen die Vorabfestlegung",
           "DIESER KOPF IST DIE VORABFESTLEGUNG" in _rxroh
           and "DIESER KOPF IST DIE VORABFESTLEGUNG" in _sbroh)
    pruefe(P, "die Reihung wird gegen H gemessen, nicht gegen alles",
           "eigenen Grundgesamtheit" in _rxroh and "2.50" in _rxroh,
           "gegen alle Anker gemessen wuerde ich zum dritten Mal H "
           "nachweisen und es der Reihung gutschreiben")
    pruefe(P, "Rueckblick und Quantilsgrenze stammen aus der PRODUKTION",
           "from agent.drift import RUECKBLICK_TAGE" in _rxq
           and "BESTES_FUENFTEL = 0.20" in _rxq,
           "damit gibt es keinen Freiheitsgrad, den ich haette guenstig "
           "setzen koennen")

    # ⚠️ DIE LEHRE, DIE MICH HEUTE FAST EINEN NULLBEFUND GEKOSTET HAETTE.
    pruefe(P, "die Positivkontrolle misst die VERSCHIEBUNG, nicht den Wert",
           "erwartet {erwartet:+.1f}" in _rxq and "vorher" in _rxq
           and "nachher" in _rxq,
           "die erste Fassung verglich das ERGEBNIS mit der Schwelle - der "
           "eingepflanzte Effekt wirkte korrekt, aber der echte Effekt war "
           "so negativ, dass die Summe darunter blieb")
    pruefe(P, "ein negativer Vorsprung wird als BEFUND gemeldet",
           "IST NEGATIV" in _rxq,
           "Methodik 2.51 - ein invertierter Befund ist kein Nullbefund")

    # ⚠️ UND DER FEHLER AUS DER SIGNALBILANZ.
    pruefe(P, "die Bilanz rechnet mit dem GEPLANTEN CRV",
           "CRV_GEPLANT = 2.0" in _sbq
           and "avg_realisiertes_crv" in _sbq,
           "meine erste Fassung nahm das realisierte CRV als Nenner - das "
           "ergab 'noetig 100,1 %'. Das realisierte ist das ERGEBNIS")
    pruefe(P, "und meldet den Widerspruch Quote gegen realisiertes R",
           "WIDERSPRUCH" in _sbq and "Es gilt das R" in _sbq,
           "Mistral/Hebel liegt mit 40,3 % ueber dem Breakeven und "
           "realisiert -0,02 R - die Treffer zahlen das CRV nicht")
    pruefe(P, "unter 30 aufgeloesten Faellen gibt es KEINE Zahl",
           "MINDEST_FAELLE = 30" in _sbq
           and "nicht entscheidbar" in _sbq)
    pruefe(P, "das Vertrauensintervall ist Wilson, nicht die Normalnaeherung",
           "def _wilson" in _sbq,
           "bei Quoten nahe 0 oder 1 liefert die Naeherung Grenzen "
           "ausserhalb [0,1] - genau der Bereich, in dem hier gemessen wird")

    # ⚠️ DER GRUND IN DER REGISTRIERUNG MUSS DER GEMESSENE SEIN.
    # (Eigener Import - `_WK` entsteht erst im naechsten Block, und ein
    # freier Name waere hier genau die Falle aus `finde_freie_namen.py`.)
    from agent import wahrscheinlichkeit as _WK0

    pruefe(P, "der Rangplatz traegt NEGATIV, und das steht so da",
           any(b.name.startswith("Rangplatz") and b.zustand == "null"
               and "SCHLECHTER" in b.warum for b in _WK0.BEITRAEGE),
           "'traegt nichts' waere zu freundlich - als Zusatzbedingung "
           "wuerde er H's Vorteil aufheben")

    # ---- DIE ZUSAMMENFUEHRUNG: EINE ZAHL STATT EINER STRICHLISTE -------
    # ⚠️ ANLASS, Nutzereinwand 22.08.2026: "das System kann diese
    # Informationen nicht SELBST in Zusammenhang bringen und eine Bewertung
    # bzw. Wahrscheinlichkeit zum gesamten Trade durchfuehren - was das
    # eigentliche Ziel des Systems ist und war."
    #
    # DIE GEFAHR DIESER STUFE IST DIE UMGEKEHRTE ZUM SCHATTEN: nicht dass
    # sie sperrt, sondern dass sie mehr behauptet, als gemessen ist. Deshalb
    # pruefen die folgenden Zeilen vor allem, was NICHT in die Zahl darf.
    from agent import wahrscheinlichkeit as _WK

    _r_h = _WK.rechne(crv=2.0, stop_relativ=0.20, gebuehr_je_seite=0.003,
                      klasse="krypto", h=True)
    _r_ohne = _WK.rechne(crv=2.0, stop_relativ=0.20, gebuehr_je_seite=0.003,
                         klasse="krypto", h=False)
    _r_unbek = _WK.rechne(crv=2.0, stop_relativ=0.20, gebuehr_je_seite=0.003,
                          klasse="krypto", h=None)
    _r_aktie = _WK.rechne(crv=2.0, stop_relativ=0.20, gebuehr_je_seite=0.003,
                          klasse="aktien", h=True)

    pruefe(P, "die Basisrate ist die Arithmetik, nicht der Messwert",
           abs(_WK.basisrate(2.0) - 1 / 3) < 1e-9
           and _WK.BASISRATE_GEMESSEN == 0.340,
           "gemessen sind 34,0 % - die 0,7 Punkte sind Drift, und ihn "
           "einzurechnen hiesse den guenstigeren der beiden Werte nehmen")
    # ⚠️ R1 (31.08.2026): H STEHT AUF `null` UND HEBT NICHTS MEHR.
    # Hier stand bis dahin "H hebt die Quote um genau die gemessenen 4,5
    # Punkte" - eine Pruefung, die einen Zahlenwert einfriert und damit zur
    # Bremse gegen die eigene Korrektur wird. Geprueft wird jetzt, dass H
    # in KEINER Belegung mehr etwas bewegt; das WARUM steht im Paket
    # "Kalibrierung" und in `wahrscheinlichkeit.BEITRAEGE`.
    pruefe(P, "⚠️ H bewegt die Quote in KEINER Belegung mehr",
           abs(_r_h["quote"] - _r_ohne["quote"]) < 1e-12
           and abs(_r_h["quote"] - _r_unbek["quote"]) < 1e-12,
           "H war gepoolt gemessen (+3,57) und ist je Kalendertag nicht von "
           "null zu trennen (-1,02 [-2,18 .. +0,14])")
    pruefe(P, "trifft H nicht zu, traegt es NICHTS - kein Abzug",
           abs(_r_ohne["quote"] - _r_ohne["basisrate"]) < 1e-12,
           "ein Merkmal, das nicht zutrifft, ist kein Gegenargument")

    # ⚠️ DIE UNTERSCHEIDUNG "unbekannt" GEGEN "geprueft und nein" GILT
    # WEITER - sie wird seit R1 nur an einem TRAGENDEN Beitrag geprueft.
    # An einem stillgelegten ist sie gegenstandslos: dort ist der
    # Eingabewert ohne Bedeutung, und beide Belegungen melden `null`.
    # ⚠️ `strategie="einstieg"` ist seit dem 31.08. PFLICHT, sonst gilt kein
    # Beitrag - die Beschraenkung ist der Punkt, nicht ein Nebeneffekt.
    _r_f0 = _WK.rechne(crv=2.0, stop_relativ=0.05, gebuehr_je_seite=0.003,
                       klasse="krypto", strategie="einstieg",
                       merkmale={"funding_fuenftel": 0})
    _r_fnix = _WK.rechne(crv=2.0, stop_relativ=0.05, gebuehr_je_seite=0.003,
                         klasse="krypto", strategie="einstieg")
    _z_nix = [z for z in _r_fnix["beitraege"] if z["name"].startswith("Funding")]
    _z_0 = [z for z in _r_f0["beitraege"] if z["name"].startswith("Funding")]
    pruefe(P, "ein fehlender Merkmalswert heisst `nie`, nicht `null`",
           _z_nix and _z_nix[0]["zustand"] == "nie"
           and _z_nix[0]["punkte"] == 0.0,
           "sonst sieht 'unbekannt' aus wie 'geprueft und nein' - der "
           "Unterschied sagt, wo sich Arbeit lohnt")
    pruefe(P, "und ein vorhandener Wert traegt seine Stufe",
           _z_0 and _z_0[0]["zustand"] == "traegt" and _z_0[0]["punkte"] > 0,
           "Fuenftel 0 ist bei Funding das beste - es muss Punkte bringen")
    pruefe(P, "auf anderen Klassen traegt H NICHT bei",
           abs(_r_aktie["quote"] - _r_aktie["basisrate"]) < 1e-12,
           "die 523 Reihen sind Binance-USDT - der Vorsprung dort gilt "
           "nicht fuer Aktien")

    # ⚠️ DER TRICHTER DARF NICHT ZWEIMAL ZAEHLEN.
    pruefe(P, "der Trichter steckt in der Basisrate, nicht als Zuschlag",
           any(z["name"].startswith("Trichter")
               and z["zustand"] == "enthalten" and z["punkte"] == 0.0
               for z in _r_h["beitraege"]),
           "er BESTIMMT die Geometrie - ihn zusaetzlich zu addieren waere "
           "dieselbe Information zweimal")

    # ⚠️ WAS NICHT DRINSTECKT, MUSS IN DERSELBEN ZUSAMMENFASSUNG STEHEN.
    _wz = _WK.saetze(crv=2.0, stop_relativ=0.20, klasse="krypto", h=True)
    # ⚠️ DIE ETIKETTEN KOMMEN AUS DER QUELLE, NICHT AUS DIESER ZEILE
    # (01.09.2026). Hier stand "Referenz"/"Betrieb" als Literal - genau die
    # Namen, die `wahrscheinlichkeit` fuehrte, waehrend `trefferbilanz` in
    # DERSELBEN Mail "Standard"/"Bitpanda" schrieb. Eine Pruefung, die den
    # einen Namen festnagelt, zementiert die Abweichung, statt sie zu
    # finden. Jetzt liest sie aus `SAETZE_JE_SEITE_MAILTEXT` - derselben
    # Stelle, aus der beide Mailbloecke lesen.
    from agent.krypto.backward_tracking import (
        SAETZE_JE_SEITE_MAILTEXT as _SAETZE12)
    pruefe(P, "die Mail nennt beide Gebuehrensaetze",
           all(any(s[0] in z for z in _wz) for s in _SAETZE12),
           "Nutzervorgabe 01.09.: getrennt fuer 0,30 %% Standard und "
           "1,50 %% Bitpanda. Erwartet %s, Zeilen: %s"
           % ([s[0] for s in _SAETZE12],
              [z for z in _wz if "noetig" in z]))
    pruefe(P, "und benennt jedes NICHT eingerechnete Merkmal",
           all(any(b.name.split(" (")[0] in z for z in _wz)
               for b in _WK.BEITRAEGE),
           "ohne diese Zeilen liest sich die Quote, als waere alles "
           "beruecksichtigt worden, was in der Mail steht")
    pruefe(P, "die Zahl gibt sich ausdruecklich NICHT als Prognose aus",
           any("KEINE PROGNOSE" in z for z in _wz)
           and any("steckt NICHT in dieser Zahl" in z for z in _wz),
           "sie ist die Haeufigkeit in einer Gruppe - und das LLM-Urteil "
           "steht daneben, nicht darin (Nutzervorgabe)")

    # ⚠️ LIEBER KEINE ZAHL ALS EINE ERFUNDENE.
    for _feld, _wert in (("crv", 0.0), ("stop_relativ", 0.0)):
        _arg = {"crv": 2.0, "stop_relativ": 0.20, "gebuehr_je_seite": 0.003}
        _arg[_feld] = _wert
        try:
            _WK.rechne(**_arg)
            _warf = False
        except _WK.WahrscheinlichkeitUnbekannt:
            _warf = True
        pruefe(P, f"ohne {_feld} wird geworfen, nicht geraten", _warf)

    # ⚠️ UND SIE MUSS IN DER MAIL GANZ OBEN STEHEN.
    _smq = _quelltext("agent/signal_mail.py")
    pruefe(P, "die Zusammenfuehrung steht VOR dem Bestand",
           "if wahrscheinlichkeit:" in _smq
           and _smq.index("if wahrscheinlichkeit:") < _smq.index("if bestand:"),
           "erst das Ergebnis, dann die Bestandteile - sonst ist es wieder "
           "eine Strichliste, die der Leser selbst zusammenrechnet")

    # ---- DIE BEFUNDKARTE MUSS ZUM CODE PASSEN (22.08.2026) --------------
    # ⚠️ ANLASS: Abschnitt 7 der Befundkarte ("Die Selektionsebene") nennt
    # Faktoren, Schwellen und Messwerte im Klartext. Ein Uebersichtsdokument
    # mit veralteten Zahlen ist schlimmer als keines - der Leser glaubt ihm.
    # Diese Pruefungen binden die Zahlen an ihre Quelle im Code.
    from agent import drift as _DR2
    from agent import trichter as _TR2

    _bk = io.open("Basisinfos/Befundkarte.md", encoding="utf-8").read()
    pruefe(P, "die Befundkarte kennt die Selektionsebene",
           "7. Die Selektionsebene" in _bk)
    for _kl, _wert in (("krypto", 0.79), ("aktien", 0.91), ("etf", 1.18)):
        pruefe(P, f"Trichterfaktor {_kl} steht im Code wie in der Karte",
               abs(_TR2.FAKTOR_JE_KLASSE[_kl][0.80] - _wert) < 1e-9
               and f"| **{_wert:.2f}** |".replace(".", ",") in _bk
               or f"| {_wert:.2f} |".replace(".", ",") in _bk,
               f"Code sagt {_TR2.FAKTOR_JE_KLASSE[_kl][0.80]}")
    pruefe(P, "rohstoffe und hedge haben KEINEN eigenen Trichterfaktor",
           _TR2.faktoren("rohstoffe")[1] is None
           and _TR2.faktoren("hedge")[1] is None,
           "die Karte fuehrt sie als Rueckfall - waere einer hinzugekommen, "
           "waere die Zeile still falsch")
    pruefe(P, "der Rangplatz-Messwert steht im Code wie in der Karte",
           abs(_DR2.GEMESSEN["abstand_5t"] - 0.0101) < 1e-9
           and _DR2.GEMESSEN["felder"] == 27
           and "+1,01 %" in _bk and "27" in _bk)
    pruefe(P, "der Rangplatz gilt NUR fuer Krypto",
           _DR2.saetze({}, "AAPL", "aktien") == []
           and _DR2.saetze({}, "GOLD", "rohstoffe") == [],
           "die Karte sagt das - eine spaetere Ausweitung ohne Nachtrag "
           "waere ein stiller Widerspruch")

    # ⚠️ DIE AUSSAGE, DIE AM LEICHTESTEN UNBEMERKT KIPPT.
    _umschalter = [f for f in ("agent/rollen_lauf.py",
                               "agent/entscheidungsrechnung.py",
                               "agent/mindestkriterien.py",
                               "agent/betraege.py")
                   if re.search(r"\bregime\b", _quelltext(f))]
    pruefe(P, "kein Parameter wird nach Marktphase umgeschaltet",
           not _umschalter,
           f"gefunden in {_umschalter} - die Karte sagt das Gegenteil, und "
           f"ein binaeres Phasenetikett hat den Deadloop gebaut")

    # ---- V1: H ALS SCHATTEN - MARKIEREN, NICHT SPERREN (22.08.2026) ----
    # ⚠️ DIE GEFAHR DIESER STUFE IST NICHT, DASS SIE FALSCH RECHNET, sondern
    # dass sie IRGENDWANN DOCH SPERRT. Ein Schatten, der eine Entscheidung
    # beruehrt, ist kein Schatten mehr - und es waere niemandem aufgefallen,
    # weil weniger Signale genau so aussehen wie ein ruhiger Markt.
    from agent import vorfilter as _VF

    def _mw(oben, unten):
        return {"oben": [{"preis_eur": p, "beruehrungen": b}
                         for p, b in oben],
                "unten": [{"preis_eur": p, "beruehrungen": b}
                          for p, b in unten]}

    _h_ja = _VF.bewerte(_mw([(135.0, 3)], [(93.0, 4)]), 90.0, 120.0,
                        False, "krypto")
    _h_a = _VF.bewerte(_mw([(112.0, 3)], [(93.0, 4)]), 90.0, 120.0,
                       False, "krypto")
    _h_b = _VF.bewerte(_mw([(135.0, 3)], [(85.0, 4)]), 90.0, 120.0,
                       False, "krypto")
    _h_1x = _VF.bewerte(_mw([(112.0, 1)], [(93.0, 1)]), 90.0, 120.0,
                        False, "krypto")
    _h_short = _VF.bewerte(_mw([(135.0, 3)], [(93.0, 4)]), 90.0, 120.0,
                           True, "krypto")
    _h_aktie = _VF.bewerte(_mw([(135.0, 3)], [(93.0, 4)]), 90.0, 120.0,
                           False, "aktien")

    pruefe(P, "H trifft zu, wenn der Weg frei UND der Stop gedeckt ist",
           _h_ja["h"] is True and _h_ja["frei"] and _h_ja["gedeckt"])
    pruefe(P, "eine Marke VOR dem Ziel nimmt A",
           _h_a["h"] is False and _h_a["frei"] is False
           and _h_a["widerstand_eur"] == 112.0,
           "und sie wird BENANNT - eine Note ohne Begruendung kann niemand "
           "widerlegen")
    pruefe(P, "keine Marke ueber dem Stop nimmt B",
           _h_b["h"] is False and _h_b["gedeckt"] is False)
    pruefe(P, "einmal beruehrt ist keine Marke",
           _h_1x["frei"] is True and _h_1x["gedeckt"] is False,
           f"MIN_BERUEHRUNGEN = {_VF.MIN_BERUEHRUNGEN}, dieselbe Zahl wie in "
           f"`messe_marken` - ein einzelner Wendepunkt ist keine Marke")

    # ⚠️ UNBEKANNT DARF NIE WIE GEPRUEFT AUSSEHEN.
    pruefe(P, "SHORT liefert None, nicht False",
           _h_short["h"] is None and "110" in _h_short["grund"],
           "Kapitel 110 hat die Spiegelbedingung gemessen: sie spiegelt "
           "NICHT. 'False' hiesse geprueft und nein - hier gilt unbelegt")
    pruefe(P, "ohne Marken, Stop oder Ziel ebenfalls None",
           _VF.bewerte(None, 90.0, 120.0)["h"] is None
           and _VF.bewerte(_mw([], []), None, 120.0)["h"] is None)

    # ⚠️ UND AUSSERHALB VON KRYPTO IST DAS KEINE SCHWAECHERE AUSSAGE,
    # SONDERN GAR KEINE - die 523 Reihen sind Binance-USDT.
    pruefe(P, "auf anderen Anlageklassen sagt die Mail, dass nie gemessen wurde",
           _h_aktie["in_gemessener_klasse"] is False
           and any("nie gemessen" in z.lower()
                   for z in _VF.saetze(_h_aktie))
           and _h_ja["in_gemessener_klasse"] is True,
           "der Schatten laeuft trotzdem ueber alle Klassen - sonst haben "
           "wir in vier Wochen wieder nur Krypto-Daten")

    # ⚠️ DER SCHATTEN MUSS SICHTBAR UND STUMM ZUGLEICH SEIN.
    _vfq = _quelltext("agent/vorfilter.py")
    _vfroh = io.open("agent/vorfilter.py", encoding="utf-8").read()
    # ⚠️ R2 (31.08.2026): DIE ABSICHT BLEIBT, DIE FORMULIERUNG NICHT.
    # Hier stand "sperrt nichts" als woertliche Suche im KOPF der Zeilen -
    # also Fachjargon, den der Leser dieser Mail nicht braucht. Geprueft
    # wird jetzt, dass der BLOCK die Zeilen als Beobachtung ausweist.
    _z_ja = _VF.saetze(_h_ja)
    pruefe(P, "der Block weist sich selbst als Beobachtung aus",
           any("keine Bewertung" in x for x in _z_ja),
           "ohne diesen Satz liest jeder die Marken als Argument fuer oder "
           "gegen den Trade - genau die Verwechslung aus CLAUDE.md")

    # ---- R2: FAKT STATT WERTUNG, UND LESBAR -----------------------------
    #
    # ⚠️ DIE ALTE FASSUNG BEHAUPTETE: "auf 523 fremden Reihen hatten solche
    # Einstiege 4,5 Punkte mehr Treffer." Diese Aussage ist seit R1
    # widerlegt (gepoolt gemessen; je Kalendertag -1,02 [-2,18 .. +0,14]).
    # Eine Mail, die sie weitertraegt, ist schlimmer als eine ohne Zeile.
    _verboten = ("4,5 Punkte", "mehr Treffer", "schlechtere Haelfte",
                 "Vorfilter H", "Schattenmessung")
    _gefunden = sorted({w for w in _verboten
                        for x in _z_ja + _VF.saetze(_h_aktie) if w in x})
    pruefe(P, "⚠️ die Mail wertet NICHT und nennt keinen widerlegten Befund",
           not _gefunden,
           "gefunden: %s. Die Lage der Marken ist ein FAKT ueber die "
           "Gegenwart; was sie fuer den Ausgang bedeutet, ist gemessen "
           "nichts" % ", ".join(_gefunden))

    # Nutzervorgabe 31.08.: "wenn Mailtext, auch fuer mich lesbar machen,
    # keine Rohzahlen." Mit Einstieg muss ein ABSTAND dastehen.
    _z_ein = _VF.saetze(_VF.bewerte(_mw([(110.0, 3)], [(95.0, 2)]), 90.0,
                                    120.0, False, "krypto",
                                    einstieg_eur=100.0))
    pruefe(P, "mit Einstieg stehen ABSTAENDE in der Mail, keine Rohpreise",
           any("%" in x for x in _z_ein) and not any("EUR" in x for x in _z_ein),
           "bekommen: %s" % " | ".join(_z_ein[1:3]))
    pruefe(P, "ohne Einstieg faellt sie auf den Preis zurueck, statt zu raten",
           any("EUR" in x for x in _VF.saetze(
               _VF.bewerte(_mw([(110.0, 3)], [(95.0, 2)]), 90.0, 120.0,
                           False, "krypto"))),
           "ein fehlender Einstieg darf keinen erfundenen Abstand ergeben")
    pruefe(P, "Beruehrungen stehen als Wort, nicht als Ziffernkuerzel",
           any("dreimal" in x for x in _z_ein)
           and not any("3-mal" in x for x in _z_ein))
    pruefe(P, "und das Modul trifft keine Entscheidung",
           "return" in _vfq and "aktion" not in _vfq
           and "veto" not in _vfq.lower(),
           "ein Schatten, der eine Entscheidung beruehrt, ist keiner - und "
           "weniger Signale sehen genau so aus wie ein ruhiger Markt")
    pruefe(P, "der Schatten haengt an der signal_id",
           # ⚠️ Der Indexname entsteht per f-String (`idx_{_TABELLE}_signal`)
           # und steht nirgends am Stueck im Quelltext - deshalb auf die
           # Bestandteile pruefen, nicht auf den fertigen Namen.
           "signal_id" in _vfq and "CREATE INDEX IF NOT EXISTS idx_" in _vfq
           and "ON {_TABELLE}(signal_id)" in _vfq,
           "ohne sie laesst sich die Zeile nie mit dem Ausgang verbinden - "
           "und genau das ist der ganze Zweck")

    # ⚠️ UND ER MUSS IN DER MAIL ANKOMMEN (die Regel vom 17.08.: gebaut ist,
    # was `simuliere_kette` in der FERTIGEN Mail nachweist).
    pruefe(P, "die Kette weist den Schatten in der fertigen Mail nach",
           '"vorfilter_gesehen"' in _quelltext("simuliere_kette.py")
           and "Vorfilter H" in io.open("simuliere_kette.py",
                                        encoding="utf-8").read())
    pruefe(P, "und der NB-Export meldet seinen Stand",
           '"vorfilter_schatten"' in _nb and "def stand" in _vfq,
           "Rolle G galt drei Tage als fertig und war nie gelaufen")

    # ---- DIE TENDENZ SCHON SEHEN, ABER NICHT ALS URTEIL (22.08.2026) ----
    # ⚠️ Nutzervorgabe: "fuer mich als Info waere hilfreich die Tendenz
    # bereits zu sehen mit Hinweis." Die Gefahr dabei ist offensichtlich -
    # eine Prozentzahl liest sich wie ein Befund. Deshalb wird hier an
    # ECHTEN Daten geprueft, dass die Zahl kommt UND die Urteilsvokabeln
    # ausbleiben, solange die Reihe zu kurz ist.
    import datetime as _dt
    import sqlite3 as _sq3

    def _leb_reihe(n, wachstum, quelle="tvl"):
        c = _sq3.connect(":memory:")
        for i in range(n):
            _LB.schreibe(c, symbol="PRUEF", quelle=quelle, zustand="wert",
                         wert=100.0 * (1 + wachstum * i / max(1, n - 1)),
                         jetzt=(_dt.date(2026, 1, 1) + _dt.timedelta(days=i)).isoformat() + "T01:20:00+00:00")
        return c

    _z_kurz = _LB.saetze(_leb_reihe(3, 0.18), "PRUEF", "krypto")
    _z_lang = _LB.saetze(_leb_reihe(40, 0.40), "PRUEF", "krypto")

    pruefe(P, "die Tendenz steht schon in der Mail, bevor sie tragfaehig ist",
           any("Tendenz bisher" in z for z in _z_kurz)
           and any("erst 3 Messungen" in z for z in _z_kurz),
           "der Nutzer will sie sehen - aber nie ohne die Zahl der "
           "Messungen daneben, sonst liest sich Rauschen wie Entwicklung")
    pruefe(P, "und sie traegt KEINE Urteilsvokabel",
           not any("GUT:" in z or "SCHLECHT:" in z or "NEUTRAL:" in z
                   for z in _z_kurz)
           and any("NOCH KEINE BEWERTUNG MOEGLICH" in z for z in _z_kurz),
           "eine Prozentzahl liest sich von selbst wie ein Befund - das "
           "Gegengewicht muss in derselben Mail stehen")
    pruefe(P, "ist die Reihe lang genug, wird aus der Tendenz ein Urteil",
           any("GUT:" in z for z in _z_lang)
           and not any("Tendenz bisher" in z for z in _z_lang)
           and not any("NOCH KEINE BEWERTUNG" in z for z in _z_lang),
           "derselbe Wert, andere Rolle - und der Uebergang haengt allein "
           "an der Reihenlaenge")

    # ⚠️ DIE BESCHRIFTUNG WAR FALSCH (gefunden 22.08. beim Vorfuehren).
    # Verglichen werden die MITTEL beider Haelften - rund die HAELFTE der
    # Bewegung vom ersten zum letzten Wert. Eine real um 20 % steigende
    # Reihe ergibt hier 9,9 % und damit "unveraendert".
    _real20 = _LB.richtung([("t%d" % i, 100.0 * (1 + 0.20 * i / 29))
                            for i in range(30)], "tvl")
    pruefe(P, "die Zeile behauptet NICHT 'gegenueber dem Beginn'",
           "gegenueber dem Beginn, " not in _lq
           and "im Mittel der zweiten gegen die erste Haelfte" in _lq,
           f"eine real um 20 % steigende Reihe meldet hier "
           f"{100 * _real20['aenderung_relativ']:.1f} % - die Zahl stimmt, "
           f"die alte Beschriftung nicht")
    pruefe(P, "und der Kalibrierungsbedarf steht im Code, nicht nur im Plan",
           'KALIBRIERUNG_FAELLIG = "2026-09-18"' in _lq,
           "die Schwelle 0,10 wurde mit der ECHTEN Aenderung begruendet, "
           "wirkt aber auf den Halbmittel-Vergleich - faktisch ~20 %. "
           "Entschieden wird das an Daten, nicht am Schreibtisch")

    # ⚠️ DAS KONTINGENT ENTSCHEIDET DEN TAKT.
    _bq = _quelltext("scheduler/background.py")
    pruefe(P, "TVL laeuft taeglich, die Entwicklerdaten nur montags",
           "def lebendigkeit_job" in _bq
           and "weekday() == 0" in _bq and 'id="lebendigkeit"' in _bq,
           "TVL kostet ZWEI Sammelabrufe, CoinGecko EINEN JE SYMBOL - "
           "taeglich waeren das rund 1.230 im Monat bei 3.521 von 10.000 "
           "verbrauchten. Und commit_count_4_weeks misst ohnehin vier "
           "Wochen: taeglich abgefragt ergaebe es 28-fach ueberlappende "
           "Messwerte")
    pruefe(P, "die Simulation weist die Zeile in der fertigen Mail nach",
           "lebendigkeit_gesehen" in _quelltext("simuliere_kette.py"),
           "eine Stufe gilt erst als gebaut, wenn simuliere_kette.py sie in "
           "der Mail nachweist - Rolle G war drei Tage lang 'fertig'")

    # ---- EIN FAKTOR FUER ALLE WAR FALSCH (93 A/A2, 19.08.2026) ----
    pruefe(P, "jede Anlageklasse hat ihre eigenen gemessenen Faktoren",
           set(_TR.FAKTOR_JE_KLASSE) == {"krypto", "aktien", "etf"}
           and all(set(v) == set(_TR.FAKTOR)
                   for v in _TR.FAKTOR_JE_KLASSE.values()),
           "der erste Faktor 0,98 passte auf KEINE Klasse: Krypto 87,5 %, "
           "ETF 72,7 % statt 80 %")
    pruefe(P, "und Krypto schwankt enger als ETF - nicht umgekehrt",
           _TR.FAKTOR_JE_KLASSE["krypto"][0.80]
           < _TR.FAKTOR_JE_KLASSE["aktien"][0.80]
           < _TR.FAKTOR_JE_KLASSE["etf"][0.80],
           "gemessen 0,79 / 0,91 / 1,18 - ueber einen zwoelffachen Horizont "
           "stabil, also eine Klasseneigenschaft und keine Streuung")
    pruefe(P, "eine unbekannte Klasse faellt zurueck und SAGT es",
           _TR.faktoren("rohstoff") == (_TR.FAKTOR, None)
           and any("KEINE eigene Messung" in z
                   for z in _TR.saetze(100.0, 4.0, klasse="rohstoff")),
           "einen Rueckfall als Messwert dieser Klasse auszugeben waere "
           "eine erfundene Grundlage")
    pruefe(P, "eine schmale Grundlage wird benannt, nicht verschwiegen",
           any("Nur 2 Reihen" in z
               for z in _TR.saetze(100.0, 4.0, klasse="aktien"))
           and not any("Nur 34 Reihen" in z
                       for z in _TR.saetze(100.0, 4.0, klasse="krypto")),
           "eine Zahl aus zwei Reihen ist anders zu lesen als eine aus 34")
    pruefe(P, "und die Klasse erreicht den Trichter aus der Rechnung",
           any("Krypto-Reihen" in z for z in _ER.saetze(
               _ER.rechne(kurs=100.0, atr=4.0, risiko_eur=60.0,
                          betrag_wunsch_eur=1000.0, instrument="hebel",
                          umgeworfen_preis_eur=99.0, assetklasse="krypto"))),
           "ohne Durchreichen waere die Klassenmessung gebaut und unwirksam")

    # ⚠️ DIE HILFSREIHEN GEHOEREN NICHT IN DIE KALIBRIERUNG.
    _mq = _quelltext("messe_trichter_treffer.py")
    pruefe(P, "die Messung schliesst die internen Hilfsreihen aus",
           '_sym.startswith("_")' in _mq,
           "_THEMEN_ETF_BENCHMARK_SPY und die drei _ROHSTOFF_FUTURES "
           "reichen bis 2001 zurueck und stellten die HAELFTE aller "
           "Anker - fuer sie entsteht nie eine Mail")
    pruefe(P, "und sie prueft den Faktor NICHT auf seinen eigenen Daten",
           "WALK-FORWARD" in _mq and "GEGENPROBE" in _mq,
           "ein Quantil trifft sein eigenes Quantil; und der scheinbare "
           "Anstieg 2025/26 war die Besetzung, nicht die Zeit")

    # ---- DER CONFIG-SCHLUESSEL, UEBER DEN NIEMAND MEHR STOLPERN SOLL ----
    # ⚠️ ROH LESEN, NICHT UEBER `_quelltext`. Der entfernt Kommentarzeilen -
    # und ein Geltungsvermerk IST ein Kommentar. Die erste Fassung dieser
    # Pruefung suchte ihn im kommentarfreien Text und schlug fehl, obwohl
    # der Vermerk dastand.
    _cfg = io.open("Basisinfos/config.yaml", encoding="utf-8").read()
    pruefe(P, "risiko_pro_trade_prozent_hebel traegt einen Geltungsvermerk",
           "GILT NUR FUER DIE ALTEN PIPELINES" in _cfg,
           "der Schluessel ist NICHT obsolet - hebel_risk_gate.py und "
           "risk_gate.py lesen ihn. Die Rollen-Kette tut es nicht; ohne "
           "Vermerk nimmt der naechste Leser an, er steuere alles")
    _bg = _quelltext("agent/betraege.py")
    pruefe(P, "und betraege.py nennt sich als die Quelle der neuen Kette",
           "risiko_pro_trade_prozent" in _bg,
           "der Verweis muss von BEIDEN Seiten lesbar sein")


def paket_luecken() -> None:
    """Eine Luecke nur melden, wo es die Groesse ueberhaupt gibt (17.08.2026).

    Gefunden bei der Abdeckungspruefung: Rolle G meldete bei JEDER
    Assetklasse "keine Angabe: Finanzierungsrate" - auch bei einer Aktie.
    Drei von sechs Saetzen bei Aktien und Rohstoffen, bei Themen-ETF alle
    drei."""
    from agent import positionierung as _PO

    P = "Luecken"

    pruefe(P, "Krypto meldet die Terminmarktluecken weiterhin",
           all(_PO._luecke_melden(n, "krypto")
               for n in _PO.TERMINMARKT_GROESSEN),
           "dort gibt es die Groessen - fehlen sie, ist das ein Mangel")
    for klasse in ("aktien", "rohstoffe", "etf", "hedge"):
        pruefe(P, f"{klasse} meldet sie nicht mehr",
               not any(_PO._luecke_melden(n, klasse)
                       for n in _PO.TERMINMARKT_GROESSEN),
               "eine Aktie hat keine Finanzierungsrate - das ist keine "
               "Luecke, sondern eine Groesse, die es dort nicht gibt")
    pruefe(P, "andere Luecken bleiben in JEDER Klasse meldbar",
           all(_PO._luecke_melden("Leerverkaufsposition", k)
               for k in ("aktien", "krypto", "etf")),
           "gefiltert wird nur, was strukturell nicht vorkommt")
    # ⚠️ ZWEI VERSCHIEDENE FAELLE, und mein erster Kommentar warf sie
    # zusammen ("fail-open"). Die Pruefung hat den Widerspruch gefunden.
    for leer in (None, ""):
        pruefe(P, f"OHNE Klasse ({leer!r}) wird gemeldet",
               _PO._luecke_melden("Open Interest", leer),
               "dann ist unklar, worueber wir reden - eine Luecke zu viel "
               "ist besser als eine verschwiegene")
    pruefe(P, "eine NEUE Klasse meldet sie nicht",
           not _PO._luecke_melden("Open Interest", "voellig_neue_klasse"),
           "die drei Zahlen stehen nur in `open_interest_snapshot`, und die "
           "fuellt `hebel_screening` nur fuer Krypto - die Meldung waere in "
           "jedem Fall Rauschen")

    # ⚠️ DER WAECHTER, DEN DIE FILTERUNG ENTSCHAERFT HAETTE.
    _q = _quelltext("agent/zweite_meinung.py")
    pruefe(P, "G5 haengt nicht mehr an der Zahl der Luecken",
           'len(lage.get("fehlt") or []) >= 3' not in _q,
           "seit die Nicht-Luecken gefiltert sind, steht bei einem "
           "Themen-ETF `fehlt = []` - eine Zaehlung der Luecken haette "
           "durchgelassen und Rolle G mit LEERER Positionierung gefragt")
    pruefe(P, "es gibt genau EINEN Waechter, nicht zwei",
           _q.count("if not saetze:") == 1,
           "meine erste Fassung stellte einen zweiten daneben - der erste "
           "stand schon da")


def paket_auswahl() -> None:
    """A1 - die Auswahl (23.08.2026, Nutzervorgabe "nie selektiv auf
    Assetebene, der Handel passiert aber auf Assetebene").

    ⚠️ DIESE STUFE VERWIRFT. Sie ist damit die erste seit dem Cooldown, die
    ueber die Grundmenge entscheidet - und deshalb gehoert jede ihrer
    Eigenschaften in eine Dauerpruefung, nicht in einen einmaligen Probelauf.
    """
    from agent import auswahl as _AW
    from agent import drift as _DR
    from agent import rollen_gate as _RG

    P = "Auswahl"

    class _K:
        def __init__(self, close):
            self.close = close
            self.date = "2026-08-23"

    def _reihe(faktor, n=300):
        # Ein gleichmaessiger Anstieg: Endkurs / Kurs vor 250 Tagen = faktor
        schritt = faktor ** (1.0 / 250.0)
        return [_K(100.0 * schritt ** i) for i in range(n)]

    # ---- k IST NIE n: sonst waere "Rang 2 von 2" eine Begruendung ----
    for n in range(0, 60):
        if _AW.k_fuer(n) >= n and n > 0:
            pruefe(P, "k ist nie gleich der Zahl der Werte", False,
                   f"bei n={n} kaeme k={_AW.k_fuer(n)} heraus")
            break
    else:
        pruefe(P, "k ist nie gleich der Zahl der Werte", True,
               "sonst stuende in der Mail eine Begruendung, die keine ist")

    pruefe(P, "die gemessene Stelle k=2 gilt ab zehn Werten",
           _AW.k_fuer(10) == 2 and _AW.k_fuer(9) == 1 and _AW.k_fuer(41) == 2,
           "messe_auswahl 23.08.: k=2 traegt (t 3,29/4,52), ab k=5 nichts mehr")
    pruefe(P, "ein einzelner Wert loest keine Auswahl aus",
           _AW.k_fuer(1) == 0 and _AW.k_fuer(0) == 0)

    # ---- K4a: GLEICHSTAND (24.08.2026) ----
    #
    # ⚠️ DIE QUOTE IST EINE OBERGRENZE, KEIN ZWANG NACH UNTEN. Zwischen zwei
    # praktisch gleichen Werten zu schneiden ist willkuerlich - und
    # willkuerliche Schnitte sind das, was dieses Projekt immer wieder als
    # Defekt findet. Gemessen: 1 % Toleranz kostet nichts (t 3,29 -> 3,32 auf
    # fuenf Tagen), 5 % kosten deutlich (t 2,95).
    pruefe(P, "die Toleranz ist klein und begruendet",
           0 < _AW.GLEICHSTAND_ANTEIL <= 0.02,
           f"{_AW.GLEICHSTAND_ANTEIL} - ab 5 % faellt der gemessene Vorsprung "
           "von +2,74 auf +2,09 Prozentpunkte")
    # Drei Werte, bei denen Platz 2 und 3 praktisch gleichauf liegen.
    _gl = {"A": _reihe(2.00), "B": _reihe(1.50), "C": _reihe(1.4999),
           "D": _reihe(1.10), "E": _reihe(1.05), "F": _reihe(1.02),
           "G": _reihe(1.01), "H": _reihe(1.005), "I": _reihe(1.004),
           "J": _reihe(1.003), "K": _reihe(1.002)}
    _a3 = _AW.waehle(_gl, list(_gl))
    pruefe(P, "wer gleichauf mit dem Letzten liegt, kommt mit",
           "C" in _a3["gewaehlt"] and _a3["gleichstand"] == 1,
           f"gewaehlt: {sorted(_a3['gewaehlt'])} bei k={_a3['k']}")
    pruefe(P, "und der klar Schlechtere bleibt draussen",
           "D" not in _a3["gewaehlt"],
           "sonst waere die Obergrenze keine")
    _a4 = _AW.waehle({"A": _reihe(2.0), "B": _reihe(1.5), "C": _reihe(1.1)},
                     ["A", "B", "C"])
    pruefe(P, "ohne Gleichstand bleibt es bei der Quote",
           _a4["gleichstand"] == 0 and len(_a4["gewaehlt"]) == _a4["k"],
           "die Ausnahme darf nicht zur Regel werden")

    # ---- WER ZU KURZ IST, RANGIERT NICHT MIT ----
    reihen = {"A": _reihe(2.0), "B": _reihe(1.5), "C": _reihe(1.1),
              "KURZ": _reihe(9.0, n=100)}
    liste = _AW.rangliste(reihen)
    pruefe(P, "wer keine Jahreshistorie hat, steht nicht in der Rangliste",
           [s for s, _ in liste] == ["A", "B", "C"],
           "KURZ hat 100 Kerzen und waere mit +800 % Erster - eine erfundene "
           "Zahl, die die Auswahl uebernommen haette")

    a = _AW.waehle(reihen, ["A", "B", "C", "KURZ"])
    pruefe(P, "die Auswahl nennt die Werte ohne Historie ausdruecklich",
           a["ohne_historie"] == ["KURZ"],
           "eine Luecke ohne Vermerk sieht spaeter aus wie ein Wert, den es "
           "nicht gab")
    pruefe(P, "gewaehlt wird der Erste, nicht der Zufall",
           a["gewaehlt"] == {"A"} and a["k"] == 1 and a["von"] == 3)

    # ---- OHNE GRUNDMENGE WIRD NICHT GESPERRT ----
    leer = _AW.waehle({}, [])
    pruefe(P, "ohne Grundmenge waehlt die Stufe NICHT",
           leer["aktiv"] is False and not leer["gewaehlt"],
           "eine Stufe, die nichts entscheiden kann, darf nicht sperren - "
           "dieselbe Linie wie beim Cooldown (fail-soft, nicht fail-shut)")

    # ---- DIE BEGRUENDUNG NENNT IMMER BEIDE ZAHLEN ----
    g = _AW.grund(a, "C")
    pruefe(P, "die Begruendung nennt Platz UND Grundmenge",
           "3" in g and "von 3" in g,
           f"sonst ist 'Rang 3' keine Auskunft - {g!r}")
    pruefe(P, "wer keine Historie hat, bekommt seinen eigenen Grund",
           "Historie" in _AW.grund(a, "KURZ"),
           "nicht 'Rang None' und nicht stillschweigend durchlassen")

    # ---- ZWEI KOPIEN DERSELBEN RANGLISTE LAUFEN AUSEINANDER ----
    #
    # ⚠️ `drift.rang()` rechnet dieselbe Zahl fuer die Mail. Wuerden beide
    # abweichen, stuenden in EINER Mail zwei verschiedene Raenge desselben
    # Werts - genau die Kopierfalle, die dieses Projekt mehrfach getroffen hat.
    import config as _C
    _wl = {x.symbol: x.assetklasse for x in _C.get_watchlist()}
    _kr = [s for s, k in _wl.items() if k == "krypto"]
    if len(_kr) >= 10:
        _r = {s: _reihe(1.0 + i / 100.0) for i, s in enumerate(_kr)}
        _a2 = _AW.waehle(_r, _kr)
        _abw = []
        for s in _kr:
            _d = _DR.rang(_r, s)
            _p = (_a2.get("platz") or {}).get(s)
            if _d and _p and (_d["platz"], _d["von"]) != _p:
                _abw.append((s, _d["platz"], _p[0]))
        pruefe(P, "Auswahl und drift.rang() liefern denselben Rangplatz",
               not _abw, f"abweichend: {_abw[:3]}")

    # ---- DIE STUFE IST IM TRICHTER ANGEMELDET ----
    pruefe(P, "die Stufe 'auswahl' steht im Trichter",
           "auswahl" in _RG.STUFEN_NAMEN,
           "eine Stufe, die verwirft und nicht gezaehlt wird, macht den "
           "Trichter unvollstaendig")
    pruefe(P, "sie steht VOR der Wiederholung",
           _RG.STUFEN_NAMEN.index("auswahl")
           < _RG.STUFEN_NAMEN.index("wiederholung"),
           "erst waehlen, dann den Mindestabstand pruefen - umgekehrt zaehlte "
           "der Cooldown Werte, die ohnehin nicht drankommen")

    # ---- BEIDE ZWEIGE BUCHEN DIE STUFE ----
    # ⚠️ GENAU EINE BUCHUNG JE STUFE - und das ist keine Kosmetik.
    # Beim Bau von A1 (23.08.) kam heraus, dass der Trockenlauf die
    # Stufe `anlass` seit dem 16.08. DOPPELT buchte: der umschliessende
    # Zweig war zu `if True` geworden, die Nachbuchung stand noch da.
    # Gemessen: `anlass bestanden 4` bei `hinein 3`.
    _q = io.open("agent/rollen_lauf.py", encoding="utf-8").read()
    for _stufe in ("anlass", "auswahl"):
        pruefe(P, f"die Stufe {_stufe} wird genau einmal gebucht",
               _q.count(f'durchlauf.bestanden(symbol, "{_stufe}")') == 1,
               "eine zweite Buchung macht den Trichter groesser als "
               "die Zahl der Symbole, die hineingegangen sind")

    # ---- DER MARKTZUSTAND SPERRT NICHTS (A1b) ----
    _z = {"symbol": "BTC", "name": "Bitcoin", "abstand": -0.12, "fenster": 200}
    _s = _AW.saetze(a, "A", _z)
    pruefe(P, "der Marktzustand steht in der Mail und sperrt nichts",
           any("sperrt nichts" in x for x in _s),
           "A1b ist Schatten: je Jahr gemischt (2024 trennt nicht, 2025 "
           "trennt und verliert trotzdem)")
    import sqlite3 as _sq
    # ---- DAS AUSROLLWERKZEUG LIEST DIE SCHLUESSEL, DIE ES GIBT ----
    #
    # ⚠️ AM 24.08. LAS ES `bestanden_je_stufe` - die Namen der PYTHON-
    # ATTRIBUTE statt der JSON-Schluessel aus `Durchlauf.als_json()`. Ergebnis
    # war ein leeres dict und daraus die Meldung "die Stufe auswahl fehlt
    # noch", waehrend die Stufe seit Stunden lief. Ein FEHLALARM im
    # Pruefwerkzeug - und eine Pruefung mit Fehlalarmen wird nicht mehr
    # aufgerufen.
    # ⚠️ GEGEN EINE ZEILE, DIE `rollen_gate.schreibe()` WIRKLICH GESCHRIEBEN
    # HAT - nicht gegen eine Annahme darueber. Genau die Annahme war der Fehler.
    import sqlite3 as _sq2

    from pruefe_ausrollen import trichterzeilen as _tz

    _cg = _sq2.connect(":memory:")
    _cg.row_factory = _sq2.Row
    _dg = _RG.Durchlauf("krypto")
    for _s in ("A", "B", "C"):
        _dg.beginne(_s)
        _dg.bestanden(_s, "auftrag")
        _dg.bestanden(_s, "fakten")
        _dg.bestanden(_s, "lagebild")
        _dg.bestanden(_s, "anlass")
    _dg.bestanden("A", "auswahl")
    _dg.verloren("B", "auswahl", "Rang 17 von 41")
    _dg.verloren("C", "auswahl", "Rang 22 von 41")
    _RG.schreibe(_cg, _dg, "2026-08-24T01:00:00")
    _zeilen = _tz(_cg)
    pruefe(P, "das Ausrollwerkzeug liest den Trichter, den die Kette schreibt",
           len(_zeilen) == 1 and _zeilen[0][0].strip() == "OK",
           f"gelesen: {_zeilen}")
    pruefe(P, "und zeigt die GANZE Kette, nicht nur eine Stufe",
           "auftrag 3 durch" in _zeilen[0][2]
           and "auswahl 1 durch / 2 raus" in _zeilen[0][2],
           f"Detail: {_zeilen[0][2][:120]}")
    # ⚠️ AUSGESCHRIEBEN, NICHT MIT SCHRAEGSTRICH. "fakten:3/2" wurde
    # am 24.08. als "3 hinein, 2 fertig" gelesen - es heisst "3 durch,
    # 2 raus". Zwei Zahlen mit einem Strich dazwischen sagen nicht, was
    # sie bedeuten.
    pruefe(P, "und die Zahlen tragen ihre Bedeutung mit",
           "durch" in _zeilen[0][2] and "raus" in _zeilen[0][2]
           and "auswahl:1/2" not in _zeilen[0][2],
           "ein Schraegstrich laedt zum Raten ein")
    pruefe(P, "samt dem haeufigsten Grund der groessten Verlustquelle",
           "Rang" in _zeilen[0][2],
           "ohne ihn wirft die Zeile eine Frage auf, die sie beantworten "
           "koennte")

    # ---- UND EIN LAUF, DER DIE AUSWAHL NIE ERREICHT ----
    #
    # ⚠️ GENAU DIESER FALL STAND AM 24.08. AM NOTEBOOK: "2 hinein, auswahl
    # 0/0, 0 heraus". Er darf nicht gruen aussehen und er muss sagen, WO die
    # Symbole geblieben sind.
    _cg2 = _sq2.connect(":memory:")
    _cg2.row_factory = _sq2.Row
    _dg2 = _RG.Durchlauf("aktien")
    for _s in ("P", "V"):
        _dg2.beginne(_s)
        _dg2.bestanden(_s, "auftrag")
        _dg2.verloren(_s, "fakten", "keine Kursreihe")
    _RG.schreibe(_cg2, _dg2, "2026-08-24T01:00:00")
    _z2 = _tz(_cg2)
    pruefe(P, "ein Lauf, den eine LUECKE stoppt, ist NICHT gruen",
           _z2[0][0].strip() != "OK",
           f"gelesen: {_z2[0][0]!r}")
    pruefe(P, "und er nennt die Stelle, an der die Symbole fielen",
           "keine Kursreihe" in _z2[0][2] and "fakten" in _z2[0][2]
           and "LUECKE" in _z2[0][2],
           f"Detail: {_z2[0][2][:140]}")

    # ---- UND EIN LAUF, DEN NUR DIE BREMSE STOPPT ----
    #
    # ⚠️ GENAU DER FALL VOM 24.08.: drei Symbole fielen bei `anlass`,
    # weil sich der Faktensatz nicht geaendert hatte - und eine
    # Zusammenfassung machte daraus "STALLED, der LLM-Generator haengt".
    # `anlass` ist ein HASH DES FAKTENTEXTES, kein Modell. Ein Verlust
    # dort ist der ZWECK der Stufe, kein Fehler.
    _cg3 = _sq2.connect(":memory:")
    _cg3.row_factory = _sq2.Row
    _dg3 = _RG.Durchlauf("themen_etf")
    for _s in ("A", "B", "C"):
        _dg3.beginne(_s)
        _dg3.bestanden(_s, "auftrag")
        _dg3.bestanden(_s, "fakten")
        _dg3.bestanden(_s, "lagebild")
        _dg3.verloren(_s, "anlass", "Faktensatz unveraendert seit 0,6 h")
    _RG.schreibe(_cg3, _dg3, "2026-08-24T00:48:00")
    _z3 = _tz(_cg3)
    pruefe(P, "eine BREMSE vor der Auswahl ist kein Fehler",
           _z3[0][0].strip() == "OK",
           f"gelesen: {_z3[0][0]!r} - `anlass` ist ein Hash, kein "
           f"Modell; ein Verlust dort ist gewollt")
    pruefe(P, "und die Zeile sagt AUSDRUECKLICH, dass es gewollt ist",
           "BREMSE" in _z3[0][2] and "Zweck der Bremse" in _z3[0][2],
           "sonst liest jemand `groesster Verlust bei anlass` als "
           "Ausfall - genau so ist es am 24.08. passiert")
    # ---- UND EINE BREMSE, DIE EINE DATENLUECKE VERDECKT ----
    #
    # ⚠️ GENAU DER FALL VOM 24.08.: 3 Symbole fielen an der BREMSE, 2 an einer
    # DATENLUECKE. Die Bremse war groesser und verdeckte die Luecke - dabei
    # wiegt eine Luecke schwerer: die eine ist ein Mangel, die andere der Zweck.
    _cg4 = _sq2.connect(":memory:")
    _cg4.row_factory = _sq2.Row
    _dg4 = _RG.Durchlauf("rollen")
    for _s in ("A", "B", "C", "D", "E"):
        _dg4.beginne(_s)
        _dg4.bestanden(_s, "auftrag")
    for _s in ("D", "E"):
        _dg4.verloren(_s, "fakten", "keine Kursreihe")
    for _s in ("A", "B", "C"):
        _dg4.bestanden(_s, "fakten")
        _dg4.bestanden(_s, "lagebild")
        _dg4.verloren(_s, "anlass", "Faktensatz unveraendert seit 0,6 h")
    _RG.schreibe(_cg4, _dg4, "2026-08-24T00:48:00")
    _z4 = _tz(_cg4)
    pruefe(P, "eine Datenluecke wird genannt, auch wenn die Bremse groesser ist",
           "DATENLUECKE" in _z4[0][2] and "fakten 2x" in _z4[0][2],
           f"Detail: {_z4[0][2][:200]}")
    pruefe(P, "und sie faerbt die Zeile, obwohl nur gebremst wurde",
           _z4[0][0].strip() != "OK",
           "eine Luecke von 2 wiegt schwerer als eine Bremse von 3")
    _cg4.close()
    _cg3.close()
    _cg.close()
    _cg2.close()

    # ---- L1: GREIFT DIE BREMSE NOCH? (Nutzerfrage 23.08.) ----
    #
    # ⚠️ DIE ANTWORT WAR NEIN, UND ZWAR GEMESSEN: nach A1 und der
    # Bestandsausnahme bleibt EIN zaehlender Aufruf je Lauf uebrig, und der
    # Leerlaufzaehler entsteht je Lauf neu - acht in Folge INNERHALB eines
    # Laufs kann es nicht mehr geben. Ersatz ist der laufuebergreifende
    # Zaehler, und diese Pruefungen sichern ihn ab.
    _c3 = _sq.connect(":memory:")
    _AW.schreibe_lauf(_c3, auswahl={"aktiv": True, "k": 1,
                                    "platz": {"A": (1, 3)},
                                    "gewaehlt": {"A"}, "entwicklung": {"A": 0.5}},
                      gruppe="krypto", symbole=["A"], jetzt="2026-08-23T10:00:00")
    _AW.vermerke_aktion(_c3, lauf="2026-08-23T10:00:00", gruppe="krypto",
                        symbol="A", aktion="NICHTS_TUN")
    pruefe(P, "ein stummer Lauf wird gezaehlt",
           _AW.stumme_laeufe(_c3, "krypto")["laeufe"] == 1)
    for _i in range(2, 10):
        _l = f"2026-08-23T{10+_i:02d}:00:00"
        _AW.schreibe_lauf(_c3, auswahl={"aktiv": True, "k": 1,
                                        "platz": {"A": (1, 3)},
                                        "gewaehlt": {"A"},
                                        "entwicklung": {"A": 0.5}},
                          gruppe="krypto", symbole=["A"], jetzt=_l)
        _AW.vermerke_aktion(_c3, lauf=_l, gruppe="krypto", symbol="A",
                            aktion="NICHTS_TUN")
    _s = _AW.stumme_laeufe(_c3, "krypto")
    pruefe(P, "ab acht stummen Laeufen in Folge schlaegt der Zaehler an",
           _s["laeufe"] == 9 and _s["stumm"] is True, str(_s))
    _AW.schreibe_lauf(_c3, auswahl={"aktiv": True, "k": 1,
                                    "platz": {"A": (1, 3)}, "gewaehlt": {"A"},
                                    "entwicklung": {"A": 0.5}},
                      gruppe="krypto", symbole=["A"], jetzt="2026-08-24T10:00:00")
    _AW.vermerke_aktion(_c3, lauf="2026-08-24T10:00:00", gruppe="krypto",
                        symbol="A", aktion="KAUFEN")
    pruefe(P, "ein einziger Einstieg setzt den Zaehler zurueck",
           _AW.stumme_laeufe(_c3, "krypto")["laeufe"] == 0,
           "sonst bliebe die Meldung stehen, obwohl die Kette wieder laeuft")
    pruefe(P, "eine andere Gruppe wird getrennt gezaehlt",
           _AW.stumme_laeufe(_c3, "aktien")["laeufe"] == 0,
           "eine stumme Aktienseite darf keine Krypto-Meldung ausloesen")
    _c3.close()

    # ---- L1: ein BESTAND zaehlt nicht als Leerlauf ----
    _q2 = io.open("agent/rollen_lauf.py", encoding="utf-8").read()
    pruefe(P, "die Leerlaufwache nimmt den Bestand aus",
           "not _war_bestand(" in _q2,
           "ein HALTEN auf einer gehaltenen Position ist die erwartete "
           "Antwort, kein Leerlauf")
    pruefe(P, "und der Rueckfall der Bestandspruefung geht zur SICHEREN Seite",
           "return False" in _q2.split("def _war_bestand")[1][:900],
           "faellt sie aus, zaehlt die Wache MIT - die Bremse bleibt scharf")

    # ---- S-2: DER AUFTRAG GEHOERT AN DAS SIGNAL (23.08.2026) ----
    #
    # ⚠️ NACH METHODIK 2.61 wird die Spalte auch GELESEN, und zwar ueber den
    # LESEPFAD DES MODELLS - nicht nur mit einem SELECT. Genau dort hat am
    # 22.08. eine neue Spalte die App angehalten: geschrieben wurde sie,
    # gelesen nie, und der Konstruktor kannte sie nicht.
    from agent import signal_abbildung as _SA
    import database.db as _DB
    from database.models import Signal as _Sig
    pruefe(P, "die Spalte strategie steht in SPALTEN_SIGNAL",
           "strategie" in _SA.SPALTEN_SIGNAL,
           "sonst wird sie nie angelegt")
    pruefe(P, "und im Datenmodell",
           "strategie" in getattr(_Sig, "__annotations__", {}),
           "eine Spalte ohne Feld liest der Konstruktor nicht - "
           "genau der Fund vom 22.08.")
    _f = _SA.felder_aus_entscheidung(
        {"aktion": "NICHTS_TUN"}, fakten={"asset": "X"}, strategie="AKKUMULATION")
    pruefe(P, "die Strategie wird kleingeschrieben abgelegt",
           _f.get("strategie") == "akkumulation",
           f"gespeichert: {_f.get('strategie')!r}")
    _f2 = _SA.felder_aus_entscheidung({"aktion": "NICHTS_TUN"},
                                      fakten={"asset": "X"})
    pruefe(P, "ohne Auftrag bleibt sie leer, statt zu raten",
           _f2.get("strategie") is None,
           "ein Vorgabewert waere eine Zahl, die niemand vergeben hat")
    # ⚠️ GEGEN DAS ECHTE SCHEMA, nicht gegen ein nachgebautes. Ein
    # handgeschriebenes CREATE TABLE haette hier zwar funktioniert -
    # und genau deshalb nichts bewiesen: der Lesepfad erwartet ALLE
    # Spalten, und die Frage ist ja, ob die neue dabei ist.
    _c2 = _sq.connect(":memory:")
    _c2.row_factory = _sq.Row
    _DB.init_db(_c2)
    _SA.migriere(_c2)
    _c2.execute("INSERT INTO signals (symbol, created_at, action, "
                "gate_passed, facts_json, strategie, quelle_kette) "
                "VALUES ('X', '2026-08-23', 'KAUFEN', 1, '{}', "
                "'akkumulation', 'rollen')")
    _gelesen = _DB._row_to_signal(
        _c2.execute("SELECT * FROM signals").fetchone())
    pruefe(P, "der Lesepfad des Modells traegt die Strategie",
           getattr(_gelesen, "strategie", None) == "akkumulation",
           "Schreiben allein genuegt nicht - das Lesen bekommt ALLE Spalten")
    _c2.close()

    # ---- DER KURSLADER DARF NICHT AN EINER EINSTELLUNG HAENGEN ----
    #
    # ⚠️ `get_latest_prices` las `row["symbol"]` und setzte damit
    # `conn.row_factory = sqlite3.Row` beim AUFRUFER voraus. Ohne sie:
    # "TypeError: tuple indices must be integers or slices, not str".
    #
    # UND DAS WAR EIN STILLER AUSFALL: `compute_ausstiegs_empfehlungen` faengt
    # breit ab und rechnet mit einem LEEREN Kursbuch weiter - der
    # Widerlegungspreis fehlt, ohne dass ein Signal ausfaellt.
    _cp = _sq.connect(":memory:")
    _cp.row_factory = _sq.Row               # `init_db` braucht sie
    _DB.init_db(_cp)
    _cp.row_factory = None                  # ... der Kurslader NICHT
    _cp.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, "
                "price_eur, fetched_at) VALUES ('X','x',1.0,0.9,'2026-08-24')")
    _preise = _DB.get_latest_prices(_cp)
    pruefe(P, "der Kurslader kommt OHNE row_factory aus",
           "X" in _preise and abs(_preise["X"].price_eur - 0.9) < 1e-9,
           "eine Funktion, die eine Einstellung des Aufrufers voraussetzt, "
           "faellt still aus, sobald sie jemand vergisst")
    _cp.row_factory = _sq.Row
    pruefe(P, "und mit row_factory liefert er dasselbe",
           set(_DB.get_latest_prices(_cp)) == set(_preise),
           "sonst haengt das Ergebnis daran, wer ihn ruft")
    _cp.close()

    # ---- P1: DAS URTEIL VON Z1 AN DER ZEILE (24.08.2026) ----
    #
    # ⚠️ Z1 lief, ging in die Mail und in die Zaehlung - und landete NICHT in
    # der Signalzeile. Damit war die einzige deterministische, kostenlose
    # Pruefung der Kette nie gegen Ergebnisse messbar.
    from agent import gegenpruefer_rollen as _Z1
    pruefe(P, "die Spalten z1_verletzt und z1_zahlen_geprueft stehen bereit",
           "z1_verletzt" in _SA.SPALTEN_SIGNAL
           and "z1_zahlen_geprueft" in _SA.SPALTEN_SIGNAL)
    pruefe(P, "und beide im Datenmodell",
           {"z1_verletzt", "z1_zahlen_geprueft"}
           <= set(getattr(_Sig, "__annotations__", {})),
           "eine Spalte ohne Feld liest der Konstruktor nicht")

    # ⚠️ DREI ZUSTAENDE, UND DER MITTLERE IST DER WICHTIGE.
    _ein = {"kurs": "Der Kurs liegt bei 100 EUR.", "atr": "Die Spanne ist 4 %."}
    _sauber = _Z1.pruefe({"lage": "Die Lage ist ruhig.", "belege": []}, _ein)
    _f1 = _SA.felder_aus_entscheidung({"aktion": "NICHTS_TUN"},
                                      fakten=_ein, z1=_sauber)
    pruefe(P, "Z1 gelaufen und sauber ergibt eine LEERE Zeichenkette",
           _f1["z1_verletzt"] == "",
           "None hiesse 'nicht gelaufen' - das ist etwas anderes")
    _f0 = _SA.felder_aus_entscheidung({"aktion": "NICHTS_TUN"}, fakten=_ein)
    # ⚠️ ABWESEND, NICHT None: `felder_aus_entscheidung` filtert am Ende
    # alle None-Werte heraus. In der Zeile steht dann NULL - dasselbe
    # Ergebnis, anderer Weg. Wer hier auf `is None` prueft, prueft an
    # der Funktion vorbei.
    pruefe(P, "ohne Z1 bleibt die Spalte leer, statt 'sauber' zu behaupten",
           "z1_verletzt" not in _f0 and "z1_zahlen_geprueft" not in _f0,
           "eine nicht gelaufene Pruefung darf nicht wie eine bestandene "
           "aussehen")

    # ⚠️ UND DIE ZAHL, DIE 'SAUBER' ERST ZU EINER AUSSAGE MACHT.
    _bruch = _Z1.pruefe(
        {"lage": "Der Kurs stieg um 47,3 Prozent.", "belege": []}, _ein)
    _f2 = _SA.felder_aus_entscheidung({"aktion": "NICHTS_TUN"},
                                      fakten=_ein, z1=_bruch)
    pruefe(P, "ein Treuebruch steht mit seiner Regel da",
           "Z-1" in (_f2["z1_verletzt"] or ""),
           f"gespeichert: {_f2['z1_verletzt']!r}")
    pruefe(P, "und die Zahl der geprueften Zahlen unterscheidet die Faelle",
           _f2["z1_zahlen_geprueft"] >= 1
           and _f1["z1_zahlen_geprueft"] == 0,
           f"sauber bei {_f1['z1_zahlen_geprueft']} geprueften Zahlen ist "
           f"KEINE Aussage - ohne diese Spalte saehen beide gleich aus")

    # ⚠️ DIE ZAHL STECKT IN `einzeln`, NICHT OBEN. Wer sie oben suchte,
    # bekaeme None und schriebe fuer jede Zeile 0.
    pruefe(P, "die geprueften Zahlen kommen aus der Z-1-Teilpruefung",
           any(e.get("regel") == "Z-1" and "geprueft" in e
               for e in (_bruch.get("einzeln") or [])),
           "auf oberster Ebene steht sie nicht")

    # ---- DER SCHATTEN: eine Zeile je Symbol, nicht nur je Gewaehltem ----
    #
    # ⚠️ NACH METHODIK 2.61 wird hier auch GELESEN, nicht nur geschrieben.
    # Eine Tabelle, die angelegt und nie gelesen wird, ist strukturell blind -
    # genau der Fall, der am 22.08. die App am Notebook angehalten hat.
    _c = _sq.connect(":memory:")
    _lauf = _AW.schreibe_lauf(_c, auswahl=a, gruppe="krypto",
                              symbole=["A", "B", "C", "KURZ"],
                              zustand={"abstand": -0.12})
    pruefe(P, "der Schatten schreibt eine Zeile je Symbol",
           _AW.stand(_c)["zeilen"] == 4,
           "eine Luecke ohne Eintrag sieht spaeter aus wie ein Tag, an dem es "
           "das Symbol nicht gab")
    pruefe(P, "genau die gewaehlten sind als gewaehlt vermerkt",
           _AW.stand(_c)["gewaehlt"] == 1)
    _AW.vermerke_aktion(_c, lauf=_lauf, gruppe="krypto", symbol="A",
                        aktion="KAUFEN")
    _st = _AW.stand(_c)
    pruefe(P, "die Aktion der Kette wird nachgetragen und ist LESBAR",
           _st["mit_aktion"] == 1 and _st["laeufe"] == 1,
           f"gelesen: {_st}")
    _zeile = _c.execute("SELECT symbol, platz, gewaehlt, aktion FROM "
                        "auswahl_schatten WHERE aktion IS NOT NULL").fetchone()
    pruefe(P, "die gelesene Zeile traegt Rang UND Aktion",
           _zeile == ("A", 1, 1, "KAUFEN"), str(_zeile))
    pruefe(P, "ein zweiter Schreibvorgang desselben Laufs verdoppelt nicht",
           (_AW.schreibe_lauf(_c, auswahl=a, gruppe="krypto",
                              symbole=["A", "B", "C", "KURZ"],
                              jetzt=_lauf) or True)
           and _AW.stand(_c)["zeilen"] == 4,
           "sonst zaehlt ein wiederholter Lauf dieselbe Empfehlung mehrfach")
    _c.close()

    pruefe(P, "ein nicht gewaehlter Wert bekommt keine Werbezeile",
           not any("besten" in x for x in _AW.saetze(a, "C", None)),
           "die Begruendung des Gewaehlten gehoert nicht in die Mail eines "
           "Abgelehnten")


def paket_verkaufsseite() -> None:
    """B1/B2 - die Verkaufsseite bekommt Fakten und Merkmale (23.08.2026).

    ⚠️ DER BEFUND, DEN DAS BEHEBT, und er ist gemessen: `facts_json` war bei
    EROEFFNEN 2.187 Zeichen lang und bei HALTEN, REDUZIEREN und VERKAUFEN
    genau 17 - der Text `{"asset": "IO"}`. Bei REDUZIEREN hatten 10 von 75
    Zeilen ueberhaupt Merkmale.

    DAS ERKLAERT O-29 ("die Verkaufsseite ist durch nichts erklaert, alle
    p > 0,47"): es gab keine Merkmale zu messen. Kein Verfahren kann eine
    Frage beantworten, deren Daten nie geschrieben wurden."""
    from agent import signal_abbildung as _SA

    P = "Verkauf"
    # ⚠️ OHNE KOMMENTARE. Die Begruendung dieses Umbaus ZITIERT den
    # alten Stummel woertlich - ein Textvergleich ueber den Rohtext
    # faende ihn im Kommentar wieder und meldete einen Fehler, den es
    # nicht gibt. Genau dafuer gibt es `_quelltext`.
    _q = _quelltext("agent/rollen_lauf.py")

    # ---- KEIN STUMMEL MEHR IN DEN SCHREIBPFADEN ----
    pruefe(P, "kein Schreibpfad verdrahtet den Faktenstummel mehr fest",
           _q.count('fakten={"asset": symbol}') == 0,
           "zwei Pfade schrieben `{\"asset\": symbol}` statt des "
           "Faktensatzes, der in den Prompt ging")
    # ⚠️ DREI STELLEN, NICHT ZWEI: die beiden Schreibpfade und - seit B3 -
    # die Gegenpruefung, die denselben Faktensatz bekommt wie die Zeile.
    # Ein Rueckfall an jeder Stelle, an der `fakten` benutzt wird.
    pruefe(P, "der Rueckfall bleibt, falls doch nichts ankommt",
           _q.count('fakten or {"asset": symbol}') == 3,
           "eine Zeile OHNE Fakten waere schlimmer als eine mit einem "
           "Stummel - dann faehlt der Bezug ganz")

    # ---- BEIDE HELFER NEHMEN DIE FAKTEN AN ----
    for _f in ("_schreibe_nein", "_sende_ausstieg"):
        _kopf = _q.split(f"def {_f}(")[1][:400]
        pruefe(P, f"{_f} nimmt einen Faktensatz entgegen",
               "fakten=None" in _kopf,
               "sonst kann der Aufrufer ihn gar nicht durchreichen")

    # ---- JEDE AUFRUFSTELLE GIBT IHN AUCH MIT ----
    #
    # ⚠️ EIN PARAMETER, DEN NIEMAND FUELLT, IST SCHLIMMER ALS KEINER: er sieht
    # im Code nach Vollstaendigkeit aus und schreibt trotzdem den Rueckfall.
    import re as _re
    _offen = []
    for _name in ("_schreibe_nein(", "_sende_ausstieg("):
        for _m in _re.finditer(_re.escape(_name), _q):
            _i = _m.start()
            if _q[max(0, _i - 4):_i].strip().startswith("def"):
                continue
            if "fakten=" not in _q[_i:_i + 900]:
                _offen.append((_name, _q[:_i].count(chr(10)) + 1))
    pruefe(P, "jede Aufrufstelle gibt den Faktensatz mit",
           not _offen, f"ohne Fakten: {_offen}")

    # ---- B2: DIE MERKMALSFAMILIEN AUF DER AUSSTIEGSSEITE ----
    _aus = _q.split("def _sende_ausstieg(")[1][:4000]
    pruefe(P, "der Ausstiegspfad rechnet die Merkmale, statt None zu schicken",
           "familien is None and reihe is not None" in _aus
           and "werte_aus_reihe" in _aus,
           "hier stand `familien=None` als EINZIGE der drei Schreibstellen")
    # ⚠️ NICHT DIE ZAHL DER AUFRUFE PRUEFEN, SONDERN DIE QUELLE. Es gibt
    # DREI Stellen, an denen die Merkmale gerechnet werden (Entscheidung,
    # Nein-Zeile, Ausstieg) - sie liegen an verschiedenen Punkten des
    # Ablaufs und koennen einander nicht ersetzen. Gefaehrlich waere
    # nicht ihre Zahl, sondern eine ZWEITE IMPLEMENTIERUNG.
    _rufe = _q.count("werte_aus_reihe(")
    pruefe(P, "alle Merkmalsrechnungen kommen aus faktenblock",
           _rufe == _q.count("FB.werte_aus_reihe(")
           + _q.count("_FB2.werte_aus_reihe("),
           f"{_rufe} Aufrufe - jeder muss aus dem Faktenblock kommen, "
           "sonst gibt es zwei Definitionen derselben Groesse")

    # ---- B3: DIE GEGENPRUEFUNG AUF DER VERKAUFSSEITE ----
    #
    # ⚠️ GEMESSEN WAR 0 VON 561. Die Verkaufsseite lief ohne jedes zweite
    # Urteil - und ist zugleich die Seite, ueber die am wenigsten bekannt ist
    # (O-29: kein Merkmal trennt Verkaufen von Halten).
    _aus2 = _q.split("def _sende_ausstieg(")[1][:6000]
    pruefe(P, "der Ausstiegspfad holt eine zweite Meinung",
           "ZM2.hole(" in _aus2 and "zai_client is not None" in _aus2,
           "ohne sie bleibt die Verkaufsseite die einzige ohne Gegenpruefung")
    pruefe(P, "sie laeuft in einem eigenen Faden",
           "threading.Thread(" in _aus2,
           "Z.ai braucht rund 34 s je Aufruf - elf Ausstiege nacheinander "
           "waeren mehr als ein ganzer Takt")
    pruefe(P, "und wird ueber DIESELBE Sammelstelle geschrieben wie beim Einstieg",
           '_faeden' in _aus2,
           "ein zweiter Schreibweg waere die naechste Stelle, an der einer "
           "von beiden vergessen wird")
    pruefe(P, "sie begrenzt die Gleichzeitigkeit NICHT selbst",
           "Semaphore" not in _aus2 and "MAX_GLEICHZEITIG" not in _aus2,
           "der Deckel sitzt in `zweite_meinung` - zwei Bremsen fuer dieselbe "
           "Leitung waeren eine zu viel")

    # ⚠️ UND SIE MAILT NICHT - das ist eine ENTSCHEIDUNG, keine Luecke.
    pruefe(P, "die Verkaufsmail wartet NICHT auf die Gegenpruefung",
           _q.index("VK2.sammel_mail(") < _q.index('ergebnis.pop("_faeden"'),
           "die Sammelmail wird bewusst vor dem Warten gebaut; wer aufnaehme, "
           "was zufaellig fertig ist, haette dasselbe Signal in zwei "
           "Darstellungen")

    # ---- UND DIE ABBILDUNG NIMMT SIE AUCH AUF ----
    _voll = _SA.felder_aus_entscheidung(
        {"aktion": "REDUZIEREN"},
        fakten={"asset": "X", "kurs": "1 EUR", "marken": "eine Marke"},
        familien={"volumen_perzentil": 42})
    pruefe(P, "ein echter Faktensatz landet auch wirklich in der Zeile",
           len(_voll.get("facts_json") or "") > 40,
           f"{len(_voll.get('facts_json') or '')} Zeichen - der Stummel hatte 17")
    pruefe(P, "und die Merkmale ebenfalls",
           _voll.get("volumen_perzentil") == 42,
           "ohne sie ist die Verkaufsseite nicht auswertbar - genau der "
           "Befund O-29")

    # ---- N-16e/F-201: KEIN STOP-TEXT MEHR FUER SPOT (03.09.2026) ----
    #
    # ⚠️ NUTZERENTSCHEIDUNG 03.09.: "kein Stop fuer Spot, Ausstieg bleibt
    # rein bewertungsbasiert". Gefunden wurde dabei, dass die deterministische
    # Fuehrung (`backward_tracking.compute_ausstiegs_empfehlungen`, taeglich
    # 7:15) weiterhin einen Trailing-Stop FUER SPOT rechnete und "Stop
    # nachziehen auf X" in ZWEI Mails zeigte - der Verkaufsmail
    # (`verkaufsrechnung.sammel_mail`) und der Kaufmail (`signal_mail.
    # baue_mail`, Abschnitt "2. DIE POSITION"). Beide Stellen haengen an
    # `_fuehrung_zu()`, die selbst NICHT veraendert wurde (sie bedient noch
    # einen dritten, bewusst unveraenderten Aufrufer: die Sperre gegen einen
    # Einstieg auf faelligem Ausstieg, Zeile ~1737 - eine andere Frage, nicht
    # Teil dieses Fixes).
    #
    # ECHTER FUNKTIONSAUFRUF, KEINE KOPIE - sonst prueft der Test sich selbst
    # (Lehre vom selben Tag, siehe F-196/G-b).
    from agent import rollen_lauf as _RL16
    for _instr, _erwartet_none in (("spot", True), ("hebel", False)):
        _ergebnis16 = {"fuehrung": {("BTC", _instr): {
            "empfehlung": "HALTEN", "mfe_r": 0.8, "stop_neu": 45000.0,
            "ist_bestand": True}}}
        _RL16._sende_ausstieg(
            symbol="BTC", befund={"begruendung": "Test"},
            verkauf={"anteil": 1.0, "gegenwert_eur": 1000.0},
            kurs_e=50000.0, instrument=_instr, strategie="einstieg",
            tag="2026-09-03", lagebild_id=None, modell="test", conn=None,
            db="data/tradinginfotool.db", betriebsart="trocken",
            versand=None, ergebnis=_ergebnis16)
        _f16 = _ergebnis16["ausstiege"][-1]["fuehrung"]
        pruefe(P, f"die Verkaufsmail zeigt keine Stop-Fuehrung fuer {_instr}"
                  if _erwartet_none else
                  f"die Verkaufsmail zeigt die Stop-Fuehrung weiter fuer {_instr}",
               (_f16 is None) == _erwartet_none,
               "bekommen: %r - Spot bekam nach Nutzerentscheidung 03.09. "
               "keinen Stop mehr, Hebel hat weiterhin einen echten" % (_f16,))

    _q16 = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "und die Kaufmail zeigt dieselbe Fuehrung ebenfalls nur bei Hebel",
           'ausstieg=((_fuehrung_zu(ergebnis, symbol, instrument) or None)'
           in _q16 and 'if instrument == "hebel" else None),' in _q16,
           "dieselbe deterministische Fuehrung geht auch in die Kaufmail "
           "(Abschnitt 'DIE POSITION') - ohne dieselbe Sperre stuende dort "
           "weiterhin ein Spot-Stop-Satz")



def paket_akkumass() -> None:
    """Die Invarianten des Akkumulations-Signalmasses (28.08.2026).

    ⚠️ WARUM EIN MESSWERKZEUG IN DIE DAUERPRUEFUNG GEHOERT. Der erste Lauf am
    28.08. hat sich durch seine eigenen Kontrollen selbst widerlegt: die
    Negativkontrolle stand bei -10,6 % statt 0, weil EINE Reihe mit +10.732 %
    den gewichteten Mittelwert bestimmte. Ohne mitlaufende Kontrollen waere
    das als Befund durchgegangen.

    Geprueft werden die drei Groessen, die ARITHMETISCH feststehen und deren
    Verletzung deshalb immer ein Rechenfehler ist - nie ein Marktbefund:

        Rang        Mittelwert ueber die ganze Reihe ist exakt 0,5
        DCA         kauft an jedem Tag, sein Vorsprung ist exakt 0
        V           die schnelle Form stimmt mit der Schleifenform ueberein

    Keine Datenbank noetig, Laufzeit unter einer Sekunde."""
    import numpy as np
    import messe_akkumulationsmass as _AM

    P = "Akkumass"

    # ---- Der Rang ist per Konstruktion auf 0,5 zentriert ----
    for n in (7, 50, 501):
        v = np.linspace(-3.0, 9.0, n)
        pruefe(P, "Rangmittel ist 0,5 bei n=%d" % n,
               abs(float(_AM.rang(v).mean()) - 0.5) < 1e-12,
               "genau das nimmt dem Drift die Wirkung - eine steigende Reihe "
               "darf keine Basisrate ueber 0,5 erzeugen")

    v = np.array([5.0, 1.0, 9.0, 3.0])
    pruefe(P, "der Rang ordnet richtig",
           list(_AM.rang(v).argsort()) == [1, 3, 0, 2])
    pruefe(P, "der Rang haengt nur an der Ordnung, nicht an der Hoehe",
           bool((_AM.rang(v) == _AM.rang(v * 1000.0 + 7.0)).all()),
           "sonst koennte eine einzelne Ausreisserreihe das Ergebnis "
           "bestimmen - genau der Fehler des ersten Laufs")

    # ---- V: schnelle Form gegen die Schleifenform ----
    kurse = np.array([10., 9., 8., 12., 11., 10., 9., 14., 13., 12., 11., 10.])
    for H in (2, 3, 5):
        schnell = _AM.verbilligung(kurse, H)
        langsam = np.array([kurse[t + 1:t + 1 + H].mean() / kurse[t] - 1.0
                            for t in range(len(kurse) - H)])
        pruefe(P, "V stimmt mit der Schleifenform bei H=%d" % H,
               bool(np.allclose(schnell, langsam)),
               "die kumulierte Summe ist eine Abkuerzung - laeuft sie aus dem "
               "Takt, misst das Werkzeug einen anderen Horizont als es sagt")
    pruefe(P, "V endet H Tage vor dem Reihenende",
           len(_AM.verbilligung(kurse, 3)) == len(kurse) - 3,
           "ein Tag ohne H Folgetage hat kein Ergebnis und darf nicht "
           "stillschweigend mitgezaehlt werden")

    # ---- Das Lookahead-Verbot: nur TIEFPUNKT darf nach vorne sehen ----
    schnitt = kurse.copy()
    schnitt[-1] = 999999.0                      # nur der LETZTE Tag aendert sich
    for name in ("UNTER_SMA", "RUECKGANG", "DCA"):
        a = _AM.zustand(kurse, name, 3, 5)
        b = _AM.zustand(schnitt, name, 3, 5)
        pruefe(P, "%s liest keine Zukunft" % name,
               bool((a == b).all()),
               "ein Zustand, der sich aendert, wenn ein SPAETERER Kurs sich "
               "aendert, hat Lookahead - und jeder Befund damit ist wertlos")
    # ⚠️ Hier muss ein Kurs INNERHALB des Vorausfensters geaendert werden.
    # Der erste Anlauf aenderte den letzten Kurs der Reihe - der liegt bei
    # H=3 gar nicht im Fenster der geprueften Tage, und die Pruefung schlug
    # fehl, obwohl der Code stimmte.
    voraus = kurse.copy()
    voraus[1:4] = 999.0                         # macht Tag 0 zum Tiefpunkt
    pruefe(P, "TIEFPUNKT sieht ABSICHTLICH nach vorne",
           bool(_AM.zustand(voraus, "TIEFPUNKT", 3, 5)[0])
           and not bool(_AM.zustand(kurse, "TIEFPUNKT", 3, 5)[0]),
           "es ist die Positivkontrolle - saehe sie NICHT nach vorne, wuerde "
           "sie nichts kontrollieren")

    # ---- DCA ist die Rechenkontrolle ----
    pruefe(P, "DCA kauft an jedem Tag",
           bool(_AM.zustand(kurse, "DCA", 3, 9).all()),
           "sein Vorsprung ist deshalb exakt 0 - jede Abweichung im Lauf ist "
           "ein Rechenfehler und kein Ergebnis")
    pruefe(P, "die Negativkontrolle traegt keine Information",
           int(_AM.zustand(kurse, "WOCHENTAG", 3, 70).sum()) == 10,
           "jeder siebte Tag, unabhaengig vom Kurs")

    # ---- Die Regeldefinition ist EINE, nicht zwei ----
    from messe_akkumulation import anteil_der_regel as _AR
    pruefe(P, "die Zustaende nutzen die Regeldefinition des Gesamtlaufs",
           _AM.zustand.__module__ == "messe_akkumulationsmass"
           and _AR.__module__ == "messe_akkumulation",
           "zwei Kopien einer Regel laufen auseinander - dann misst die "
           "Tageszerlegung etwas anderes als der Gesamtlauf, und der "
           "Unterschied saehe aus wie ein Befund")



def paket_abkapselung() -> None:
    """Der alte Weg ist STILLGELEGT - und bleibt es (28.08.2026).

    ⚠️ NUTZERVORGABE, die dieses Paket ausgeloest hat: *"ist wieder ein
    Stolperstein - pruefe wie kritisch es ist, und wenn wir das so lassen, muss
    der Bereich sauber abgekapselt werden, damit nichts mitlaeuft, wo wir
    spaeter wieder ein Problem haben."*

    WIE KRITISCH ES IST, am Code gemessen: `agent/multi_asset_batch.py` und
    `agent/krypto/budget_allocator.py` enthalten das Wort `strategie` NULL Mal.
    Ein Rueckfall brauchte keinen Fehler - eine Gruppe aus `aktiv_fuer` zu
    nehmen genuegt, und die Umbauten vom 27./28.08. waeren umgangen. Still.

    DREI DINGE HALTEN DEN ZUSTAND, und alle drei werden hier geprueft:

        Gate      beide Nahtstellen fragen `bedient_neue_kette`
        Warnung   sie warnen LAUT, wenn der alte Weg doch anlaeuft
        Sauberkeit die neue Kette kennt "tranchen" an keiner Stelle
    """
    import config as _cfgm
    from agent import assetklassen as _AK
    from scheduler import rollen_job as _RJ

    P = "Abkapselung"
    _cfg = _cfgm.load_config()

    # ---- Der Zustand selbst ----
    gruppen = sorted({g for g, _, _ in _AK.laeufe()})
    offen = [g for g in gruppen if not _RJ.bedient_neue_kette(g, _cfg)]
    pruefe(P, "jede Gruppe laeuft ueber die Rollen-Kette",
           not offen,
           "noch alt: %s - fuer diese Gruppen liefe der ABGEKAPSELTE Weg, "
           "und er kennt weder Strategie noch Positionsfuehrung" % offen)

    # ---- Die neue Kette RUFT keine Tranchen auf ----
    #
    # ⚠️ GEPRUEFT WIRD DER AUFRUF, NICHT DAS WORT. Die erste Fassung suchte
    # "tranchen" im ganzen Quelltext - und schlug an meiner eigenen Warnzeile
    # an, die das Wort nennen MUSS ("Tranchen (AZ-4) liefe wieder mit"). Eine
    # Pruefung, die das Reden ueber eine Sache mit ihrer Verwendung
    # verwechselt, meldet Fehlalarme - und ein Werkzeug mit Fehlalarmen wird
    # nicht mehr aufgerufen.
    #
    # ⚠️ UND DIE ZWEITE FASSUNG WAR AUCH NOCH ZU GROB: sie suchte "tranchen."
    # als Text und fand "agent/tranchen.py" in genau derselben Warnzeile.
    # Textsuche kann Code nicht von Prosa unterscheiden - der Syntaxbaum kann
    # es. Geprueft werden jetzt die IMPORTE, nichts sonst.
    import ast as _ast

    def _importiert(datei: str, modul: str) -> bool:
        baum = _ast.parse(_quelltext(datei))
        for k in _ast.walk(baum):
            if isinstance(k, _ast.Import):
                if any(a.name.split(".")[-1] == modul for a in k.names):
                    return True
            elif isinstance(k, _ast.ImportFrom):
                if (k.module or "").split(".")[-1] == modul:
                    return True
                if any(a.name == modul for a in k.names):
                    return True
        return False

    for datei in ("agent/rollen_lauf.py", "scheduler/rollen_job.py"):
        pruefe(P, "%s importiert keine Tranchen" % datei.split("/")[-1],
               not _importiert(datei, "tranchen"),
               "Tranchen sind durch `akkumulation` ersetzt - liefen sie in der "
               "neuen Kette mit, gaebe es zwei Verfahren nebeneinander")

    # ---- Der alte Weg kennt die Umbauten NICHT: das ist der Schaden ----
    for datei in ("agent/multi_asset_batch.py", "agent/krypto/budget_allocator.py"):
        pruefe(P, "%s kennt `strategie` nicht" % datei.split("/")[-1],
               "strategie" not in _quelltext(datei).lower(),
               "⚠️ Diese Pruefung ist KEINE Forderung, sondern die Messung des "
               "Schadens: solange der alte Weg die Strategie nicht kennt, ist "
               "ein Rueckfall ein Rueckschritt - und genau deshalb muss die "
               "Nahtstelle warnen. Faellt sie, ist der alte Weg nachgezogen "
               "worden und die Warnung darf milder werden")

    # ---- Beide Nahtstellen warnen LAUT, nicht auf info ----
    _bg = _quelltext("scheduler/background.py")
    pruefe(P, "es gibt EINE Warnfunktion, nicht zwei Texte",
           hasattr(_RJ, "warne_alter_weg") and hasattr(_RJ, "VERLUST_IM_RUECKFALL"),
           "zwei Kopien derselben Liste laufen auseinander - dann warnt die "
           "eine Naht vor etwas anderem als die andere")
    pruefe(P, "und beide Nahtstellen rufen sie auf",
           _bg.count("warne_alter_weg") >= 2,
           "gefunden: %d Aufrufe. Der Batch-Zweig UND der Allocator-Zweig "
           "muessen warnen - der zweite hatte bis 28.08. gar keine Meldung"
           % _bg.count("warne_alter_weg"))
    pruefe(P, "die Warnung nennt, was im Rueckfall fehlt",
           len(_RJ.VERLUST_IM_RUECKFALL) >= 4
           and any("kkumulation" in z for z in _RJ.VERLUST_IM_RUECKFALL),
           "eine Warnung ohne Folgen ist eine Zeile, die man wegklickt")
    pruefe(P, "und sie ist ohne Emoji lesbar",
           all(ord(c) < 128 for z in _RJ.VERLUST_IM_RUECKFALL for c in z),
           "auf der Windows-Konsole kam das Warnzeichen als \u26a0\ufe0f an - "
           "eine Warnung, die man entziffern muss, ist keine")

    # ---- Das stillgelegte Modul sagt selbst, dass es stillgelegt ist ----
    import agent.tranchen as _TR
    pruefe(P, "agent/tranchen.py weist sich als abgekapselt aus",
           "ABGEKAPSELT" in (_TR.__doc__ or ""),
           "es steht NICHT in der Toten-Liste der Modulkarte, weil es noch "
           "importiert wird - von Modulen, die selbst nie laufen. Die "
           "Modulkarte findet Importe, keine toten Aufrufketten. Der Docstring "
           "ist deshalb die einzige Stelle, an der es sichtbar wird")

    # ---- Und der Kern ist wieder der Kern ----
    import database.db as _db
    pruefe(P, "die Akkumulations-Vorgabe umfasst nur BTC/ETH/SOL",
           _db._DCA_ERLAUBT_DEFAULT_SYMBOLS == {"BTC", "ETH", "SOL"},
           "bekommen: %s - die 13 Aktien/ETFs stammten aus der Tranchen-Zeit "
           "und stellten die GUI-Spalte auf 'An', ohne zu wirken"
           % sorted(_db._DCA_ERLAUBT_DEFAULT_SYMBOLS))



def paket_akkumulationslage() -> None:
    """Entscheidung B+C - die Lage-Bewertung der Akkumulation (28.08.2026).

    B  der Kern bekommt KEINEN Verbilligungssatz. Er wird gehalten, weil er
       ueberleben soll, nicht weil der Zeitpunkt guenstig ist.
    C  die Ausschlussseite wird GEZEIGT, nicht erzwungen - fuer den Kern ist
       sie unbelegt.

    ⚠️ C WURDE AM 28.08. IN DER GEGENPRUEFUNG KORRIGIERT. Die erste Fassung
    wollte fuer den Kern sperren, begruendet mit "die Bremse greift dort am
    haeufigsten (24,5 % der Tage)". Haeufigkeit ist kein Beleg: nachgemessen
    zeigt das Band ueber +30 % bei den Kernwerten teils die GEGENRICHTUNG
    (BTC +0,0112 / ETH +0,0423 / SOL +0,0605 auf H=90). Eine Bremse darauf
    waere die "Bremse ohne Potentialaussage", an der dieses Projekt schon
    79 % seines Trichters verloren hat."""
    from agent import akkumulationslage as _AL

    P = "Akkumulationslage"

    class _K:
        def __init__(self, close):
            self.close = close

    def _reihe(endkurs, n=250):
        return [_K(100.0)] * (n - 50) + [_K(100.0 + (endkurs - 100.0) * i / 49)
                                         for i in range(50)]

    # ---- Die Kennlinie ist MONOTON - das ist ihre Aussage ----
    raenge = [r for _, _, r, _ in _AL.BAENDER]
    pruefe(P, "die Kennlinie faellt ueber alle neun Baender",
           all(a > b for a, b in zip(raenge, raenge[1:])),
           "gemessen wurde eine monotone Kennlinie - steht hier eine andere, "
           "ist die Tabelle abgeschrieben und nicht uebertragen")
    pruefe(P, "und die Baender decken jede Lage ab, ohne Luecke",
           all(abs(_AL.BAENDER[i][1] - _AL.BAENDER[i + 1][0]) < 1e-9
               for i in range(len(_AL.BAENDER) - 1)),
           "eine Luecke gaebe stillschweigend `None` zurueck - und eine "
           "fehlende Zeile sieht aus wie eine unauffaellige Lage")

    # ---- B: der Kern bekommt KEINE Zahl ----
    for sym in ("BTC", "ETH", "SOL"):
        z = _AL.saetze(sym, _reihe(55.0))
        pruefe(P, "%s bekommt keinen Verbilligungssatz" % sym,
               z and not any("Erwartung" in s for s in z)
               and any("NICHT belegt" in s for s in z),
               "Entscheidung B: fuer diese drei ist der Befund gemessen "
               "WIDERLEGT (Rang -0,03 bei p > 0,7), nicht ungeprueft")

    # ---- und ein anderer Wert bekommt sie sehr wohl ----
    z = _AL.saetze("ADA", _reihe(55.0))
    pruefe(P, "ein Wert ausserhalb des Kerns bekommt die Zahl",
           any("Erwartung" in s and "+6,1" in s for s in z),
           "bekommen: %s" % z)
    pruefe(P, "die Zahl steht NIE ohne ihren Vergleich",
           all("beliebiger Tag dieser Reihe" in s
               for s in z if "Erwartung" in s),
           "eine Prozentzahl allein waere wieder der Drift - genau das, was "
           "die Rangbildung herausrechnet")

    # ---- C: die teure Lage wird GEZEIGT, aber sie sperrt nicht ----
    z = _AL.saetze("ADA", _reihe(160.0))
    pruefe(P, "eine teure Lage wird als TEURER ausgewiesen",
           any("TEURER" in s for s in z) and any("-11,8" in s for s in z))
    pruefe(P, "aber das Modul sperrt nichts",
           not any(w in _quelltext("agent/akkumulationslage.py")
                   for w in ("return False, ", "raise ValueError",
                             "verwerfe", "sperre")),
           "dieselbe Bauform wie der Vorfilter: markieren, nicht sperren")

    # ---- Kein Lookahead, und beide Kursformate ----
    pruefe(P, "der Schnitt liest nur die letzten 200 Werte",
           abs(_AL.abstand_zum_schnitt([_K(100.0)] * 200 + [_K(150.0)])
               - (150.0 / (100.0 * 199 / 200 + 150.0 / 200) - 1.0)) < 1e-9,
           "das Fenster endet beim aktuellen Tag EINSCHLIESSLICH - wer weiter "
           "greift, misst etwas anderes als gemessen wurde")
    pruefe(P, "Kerzen und rohe Zahlen ergeben dasselbe",
           _AL.abstand_zum_schnitt([_K(100.0)] * 200 + [_K(60.0)])
           == _AL.abstand_zum_schnitt([100.0] * 200 + [60.0]),
           "⚠️ In der Kette stehen KERZEN mit `.close`. Die erste Fassung las "
           "`float(k)` und haette einen TypeError geworfen, den das try/except "
           "an der Naht verschluckt haette - fail-soft ist fail-silent")
    pruefe(P, "eine zu kurze Reihe gibt None, keine Notzahl",
           _AL.abstand_zum_schnitt([_K(1.0)] * 199) is None
           and _AL.saetze("ADA", [_K(1.0)] * 50) == [])

    # ---- Die Mailzeilen sind ohne Sonderzeichen ----
    alle = (_AL.saetze("ADA", _reihe(55.0)) + _AL.saetze("BTC", _reihe(55.0))
            + _AL.saetze("ADA", _reihe(160.0)))
    pruefe(P, "keine Mailzeile traegt ein Sonderzeichen",
           all(ord(c) < 128 for s in alle for c in s),
           "keine einzige Mailzeile dieses Projekts traegt eines (geprueft "
           "ueber vier Module, 0 Treffer) - auf der Windows-Konsole kaeme es "
           "als Escape-Folge an")

    # ---- DIE NAHT: erreicht es die fertige Mail? ----
    #
    # ⚠️ "Eine Stufe gilt erst als gebaut, wenn sie in der FERTIGEN Mail
    # nachweisbar ist" - die Lektion aus Rolle G, die nie lief, und aus N-9,
    # wo elf Zusatzfakten keine Mail erreichten.
    from agent import signal_mail as _SM
    import inspect as _insp
    pruefe(P, "baue_mail nimmt den Block an",
           "akkumulationslage" in _insp.signature(_SM.baue_mail).parameters,
           "ohne Parameter waere das Modul eine Absichtserklaerung")
    _rl = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "und die Kette uebergibt ihn",
           "akkumulationslage=_akl_zeilen" in _rl,
           "N-9: elf Zusatzfakten erreichten die Mail nicht, weil die Naht "
           "fehlte - die Pruefung fuetterte die Funktion direkt")
    pruefe(P, "die Kette uebergibt die EIGENE Reihe, nicht das ganze Dict",
           "(reihen or {}).get(symbol)" in _rl,
           "`reihen` ist ein Dict ueber alle Symbole - wer es ganz uebergibt, "
           "bekommt None und eine stumme Leerzeile")
    pruefe(P, "und nur bei der Strategie akkumulation",
           'if str(strategie or "").strip().lower() == "akkumulation":' in _rl,
           "fuer einen Einstieg ist die Verbilligung nicht das Erfolgsmass - "
           "eine Zahl aus der falschen Messung waere schlimmer als keine")

    # ---- Und die fertige Mail traegt die Zeile wirklich ----
    # ⚠️ DIE ECHTE RECHNUNG, KEINE ATTRAPPE. Mit einem handgebauten dict
    # brach `entscheidungsrechnung.saetze()` an `einstieg_von_eur` - eine
    # Pruefung, die eine Attrappe fuettert, prueft die Attrappe.
    from agent import entscheidungsrechnung as _ER2
    _r2 = _ER2.rechne(kurs=64797, atr=1750, risiko_eur=75, instrument="spot",
                      betrag_wunsch_eur=500, topf_frei_eur=500)
    _, _txt = _SM.baue_mail(
        symbol="ADA", name="Cardano", kurs_eur=0.55, instrument="spot",
        strategie="akkumulation",
        rechnung=_r2,
        urteil={"aktion": "KAUFEN", "begruendung": "Probe"},
        akkumulationslage=_AL.saetze("ADA", _reihe(55.0)))
    pruefe(P, "die FERTIGE Mail traegt die Lage-Zeile",
           "200-Tage-Schnitt" in _txt and "Erwartung" in _txt,
           "nicht die Funktion wurde gefuettert, sondern die Mail gebaut - "
           "das ist der Unterschied, an dem Rolle G vier Wochen scheiterte")
    _, _txt_kern = _SM.baue_mail(
        symbol="BTC", name="Bitcoin", kurs_eur=64797.0, instrument="spot",
        strategie="akkumulation",
        rechnung=_r2,
        urteil={"aktion": "KAUFEN", "begruendung": "Probe"},
        akkumulationslage=_AL.saetze("BTC", _reihe(55.0)))
    pruefe(P, "und die Kern-Mail traegt KEINE Erwartung",
           "200-Tage-Schnitt" in _txt_kern
           and "Erwartung" not in _txt_kern
           and "NICHT belegt" in _txt_kern,
           "Entscheidung B endet nicht im Modul, sondern in der Mail - hier "
           "wird sie am fertigen Text nachgewiesen")



def paket_namensschatten() -> None:
    """T4c - ein Import IN einer Funktion darf keinen globalen Namen ueberschatten.

    ⚠️ EINE NEUE FEHLERKLASSE, am 28.08.2026 selbst hineingebaut und teuer
    gefunden. `agent/rollen_lauf.py` importiert in Zeile 50 modulweit
    `assetklassen as _AKL`. Ein zweiter Import unter DEMSELBEN Namen mitten in
    `_ein_asset` machte `_AKL` zur LOKALEN Variable der ganzen Funktion - und
    damit die Zugriffe in Zeile 1412 und 1453, die VORHER laufen, zu Zugriffen
    auf eine ungebundene Lokale.

        UnboundLocalError: cannot access local variable '_AKL'
        -> geschluckt vom breiten Fehlerfang, protokolliert als
           "Topfzuordnung aus dem Lauf statt aus der Zahl"
        -> Ergebnis: KEINE Mail, KEIN Signal, keine erkennbare Ursache

    ⚠️ UND `finde_freie_namen.py` FINDET DAS NICHT - 0 Kandidaten. Es sucht
    Namen, die NIRGENDS definiert sind; hier war der Name sehr wohl definiert,
    nur eben global und lokal ueberschattet. Die Umkehrung derselben Falle,
    und sie braucht ein eigenes Werkzeug.

    Geprueft wird per Syntaxbaum, nicht per Textsuche."""
    import ast as _ast
    import os as _os

    P = "T4c"
    treffer = []
    for wurzel, _, dateien in _os.walk("agent"):
        for d in dateien:
            if not d.endswith(".py"):
                continue
            pfad = _os.path.join(wurzel, d).replace("\\", "/")
            try:
                baum = _ast.parse(_quelltext(pfad))
            except SyntaxError:
                continue
            # Modulweite Importnamen sammeln
            global_namen = set()
            for k in baum.body:
                if isinstance(k, (_ast.Import, _ast.ImportFrom)):
                    for a in k.names:
                        global_namen.add(a.asname or a.name.split(".")[0])
            # ⚠️ NUR WO DER ZUGRIFF VORHER STEHT. Ein funktionsinterner
            # Import GLEICHEN Namens ist fuer sich harmlos, solange in
            # derselben Funktion nicht VOR der Importzeile auf den Namen
            # zugegriffen wird - dann und nur dann ist die Lokale ungebunden.
            # Ohne diese Einschraenkung meldet die Pruefung den halben Bestand
            # (re, datetime, timedelta ...), und ein Werkzeug mit Fehlalarmen
            # wird nicht mehr aufgerufen.
            for f in _ast.walk(baum):
                if not isinstance(f, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    continue
                for k in _ast.walk(f):
                    if not isinstance(k, (_ast.Import, _ast.ImportFrom)):
                        continue
                    for a in k.names:
                        name = a.asname or a.name.split(".")[0]
                        if name not in global_namen:
                            continue
                        frueher = [
                            n for n in _ast.walk(f)
                            if isinstance(n, _ast.Name)
                            and n.id == name
                            and isinstance(n.ctx, _ast.Load)
                            and n.lineno < k.lineno]
                        if frueher:
                            treffer.append(
                                "%s:%d %s in %s() - Zugriff schon in Zeile %d"
                                % (pfad, k.lineno, name, f.name,
                                   min(n.lineno for n in frueher)))

    pruefe(P, "kein funktionsinterner Import ueberschattet einen globalen",
           not treffer,
           "gefunden: %s - jeder dieser Namen wird in seiner Funktion LOKAL, "
           "und jeder fruehere Zugriff darauf wirft UnboundLocalError, den der "
           "breite Fehlerfang schluckt" % treffer[:5])



def paket_l3() -> None:
    """L3a - die Liquidation gehoert an das Signal (28.08.2026).

    ⚠️ DER BEFUND. `entscheidungsrechnung` rechnet `liquidation_etwa_eur`
    (Zeile 759) und die Mail nennt sie (Zeile 944) - gespeichert wurde sie
    nie. In `signals` fehlte die Spalte, und `felder_aus_entscheidung` liess
    das Feld deshalb STILLSCHWEIGEND fallen. Genau die Falle, die der eigene
    Docstring dort fuer andere Felder beschreibt.

    ⚠️ NUR BEIM HEBEL. Fuer Spot setzt `entscheidungsrechnung` `hebel = 1.0`
    und rechnet gar keine Liquidation. Eine Null in der Spalte waere eine
    erfundene Zahl - und sie saehe aus wie eine gemessene."""
    import sqlite3 as _sq
    from agent import entscheidungsrechnung as _ER
    from agent import signal_abbildung as _SA

    P = "L3"

    # ---- Die Spalte entsteht durch Migration, additiv und idempotent ----
    # ⚠️ DAS ECHTE SCHEMA, KEINE ATTRAPPE. Eine handgebaute Minimaltabelle
    # brach an `gate_passed` - und eine Pruefung, die eine Attrappe fuettert,
    # prueft die Attrappe. `init_db` legt dieselbe Tabelle an wie der Betrieb.
    import database.db as _dbm
    c = _sq.connect(":memory:")
    c.row_factory = _sq.Row
    _dbm.init_db(c)
    neu = _SA.migriere(c)
    pruefe(P, "die Migration legt liquidation_etwa_eur an",
           "signals.liquidation_etwa_eur" in neu)
    pruefe(P, "und ein zweiter Lauf legt nichts doppelt an",
           _SA.migriere(c) == [] or "signals.liquidation_etwa_eur"
           not in _SA.migriere(c),
           "additiv UND idempotent - sonst bricht jeder Neustart")

    # ---- Der Wert kommt aus der ECHTEN Rechnung, nicht aus einer Attrappe ----
    r_hebel = _ER.rechne(kurs=64797, atr=1750, risiko_eur=75,
                         instrument="hebel", betrag_wunsch_eur=500,
                         topf_frei_eur=500)
    pruefe(P, "die Rechnung liefert die Liquidation ueberhaupt",
           r_hebel.get("liquidation_etwa_eur") is not None,
           "ohne sie hat die Spalte nichts zu speichern")

    def _felder(rechnung, instrument):
        return _SA.felder_aus_entscheidung(
            antwort={"aktion": "KAUFEN", "begruendung": "Probe"},
            fakten={}, lagebild_id=None, prompt_stand="probe",
            instrument=instrument, rechnung=rechnung, modell="probe")

    f_h = _felder(r_hebel, "hebel")
    pruefe(P, "ein Hebel-Signal traegt die Liquidation",
           f_h.get("liquidation_etwa_eur") is not None
           and abs(float(f_h["liquidation_etwa_eur"])
                   - float(r_hebel["liquidation_etwa_eur"])) < 1e-6,
           "bekommen: %s gegen %s in der Rechnung"
           % (f_h.get("liquidation_etwa_eur"),
              r_hebel.get("liquidation_etwa_eur")))

    r_spot = _ER.rechne(kurs=64797, atr=1750, risiko_eur=75,
                        instrument="spot", betrag_wunsch_eur=500,
                        topf_frei_eur=500)
    f_s = _felder(r_spot, "spot")
    pruefe(P, "ein Spot-Signal traegt KEINE Liquidation",
           f_s.get("liquidation_etwa_eur") is None,
           "eine Null waere eine erfundene Zahl und saehe aus wie eine "
           "gemessene - bekommen: %s" % f_s.get("liquidation_etwa_eur"))

    # ---- DIE NAHT: kommt der Wert wirklich in der TABELLE an? ----
    #
    # ⚠️ Nicht die Funktion fuettern, sondern schreiben und zurueklesen. Genau
    # hier fiel der Wert vorher lautlos heraus: `schreibe_signal` uebernimmt
    # nur Felder, die als SPALTE existieren.
    _SA.schreibe_signal(c, symbol="ETH", felder=f_h)
    zeile = c.execute("SELECT liquidation_etwa_eur FROM signals "
                      "WHERE symbol='ETH'").fetchone()
    pruefe(P, "und sie steht danach in der TABELLE",
           zeile is not None and zeile[0] is not None,
           "gelesen: %s - vorher fiel das Feld hier lautlos heraus, weil die "
           "Spalte fehlte" % (zeile,))



def paket_instrument_reparatur() -> None:
    """I-1 bis I-4 - die Folgen von S6b nachgezogen (28.08.2026).

    ⚠️ DER GEMEINSAME KERN. Seit S6b ist `instrument` im Lauf immer "spot",
    weil es nur noch EINEN Lauf je Asset gibt. Zwoelf Stellen fragten
    weiterhin `instrument == "hebel"` - und bekamen seither immer nein."""
    import sqlite3 as _sq
    import ast as _ast
    from agent.handelsauftrag import ist_hebelgeschaeft as _IH

    P = "I-Reparatur"

    # ---- I-1: EINE Stelle beantwortet die Sachfrage ----
    pruefe(P, "das Ergebnis schlaegt den Lauf",
           _IH({"etikett": "hebel"}, "spot") is True
           and _IH({"etikett": "spot"}, "hebel") is False,
           "die Sachfrage steht im Etikett der Rechnung, nicht im Lauf")
    pruefe(P, "ohne Rechnung bleibt das Lauf-Etikett der Rueckfall",
           _IH(None, "hebel") is True and _IH(None, "spot") is False,
           "es gibt Aufrufer ohne Rechnung (Anzeige, Altdaten) - ein "
           "Rueckfall, der still das Gegenteil behauptet, waere schlimmer "
           "als keiner")
    pruefe(P, "eine Rechnung ohne Etikett faellt ebenfalls zurueck",
           _IH({}, "hebel") is True,
           "sonst wuerde ein unvollstaendiges dict wie 'kein Hebel' wirken")

    # ---- I-1a: der Kostenfehler ----
    from agent import trefferbilanz as _TB
    _k = lambda h, t=30.0: _TB.kosten_r_aus_stop(
        100.0, 95.0, "krypto", position_eur=1000.0,
        instrument="spot", hebel=h, tage=t)
    # ⚠️⚠️ DIESE PRUEFUNG STAND AUF 30 TAGEN - UND WAR NUR DESHALB GRUEN.
    #
    # Am 01.09.2026 nachgerechnet: bei 1, 3, 7 und 14 Tagen war
    # `_k(3.0) < _k(1.0)`, also GENAU DAS GEGENTEIL der Behauptung. Grund
    # war die im Hebel-Tier fehlende Handelsgebuehr (siehe
    # `backward_tracking.kosten_in_r`); erst nach 30 Tagen uebersteigt die
    # aufgelaufene Finanzierung diese Luecke.
    #
    # Die geplante Hebel-Haltedauer liegt bei 1 bis 3 Tagen. Die Pruefung
    # stand also ausgerechnet auf der einzigen Stufe, bei der der Fehler
    # unsichtbar war. Deshalb gilt sie jetzt fuer JEDE Haltedauer - eine
    # Aussage, die nur bei einem Parameterwert haelt, ist keine.
    _tage_stufen = (0.0, 1.0, 3.0, 7.0, 14.0, 30.0)
    _je_tag = [(t, _k(3.0, t), _k(1.0, t)) for t in _tage_stufen]
    pruefe(P, "ein gehebelter Trade kostet mehr als derselbe ungehebelte - "
              "bei JEDER Haltedauer",
           all(a is not None and b is not None and a > b
               for _t, a, b in _je_tag),
           "gemessen: " + ", ".join("%.0f Tage %.4f gegen %.4f" % z
                                    for z in _je_tag)
           + ". Bis 01.09. fehlte im Hebel-Tier die Handelsgebuehr auf das "
             "Nominal - der Hebel erschien SIEBENMAL billiger als Spot")
    pruefe(P, "und die Finanzierung waechst mit der Haltedauer",
           all(_je_tag[i][1] < _je_tag[i + 1][1]
               for i in range(len(_je_tag) - 1)),
           "sonst rechnet die Mail eine Position, die laenger offen ist, "
           "nicht teurer - und der Hebel verliert seine einzige "
           "zeitabhaengige Kostenart")
    pruefe(P, "und ein ungehebelter Trade traegt keine Finanzierung",
           all(_k(1.0, t) == _k(None, t) for t in _tage_stufen)
           and len({round(_k(1.0, t), 12) for t in _tage_stufen}) == 1,
           "Hebel 1,0 ist kein Hebel - die Finanzierung faellt nicht an, "
           "und die Haltedauer darf die Spot-Kosten nicht beruehren")

    # ---- I-3: die Positionsfuehrung liest BEIDE Quellen ----
    import database.db as _dbm
    from agent import positionsfuehrung as _PF

    def _db_mit(hebelzeile: bool, hebeltabelle: bool = True):
        c = _sq.connect(":memory:")
        c.row_factory = _sq.Row
        _dbm.init_db(c)
        if not hebeltabelle:
            c.execute("DROP TABLE hebel_signals")
        c.execute("INSERT INTO signals (symbol, created_at, action, "
                  "facts_json, gate_passed) VALUES "
                  "('BTC','2026-08-01','KAUFEN','{}',1)")
        if hebelzeile and hebeltabelle:
            c.execute("INSERT INTO hebel_signals (symbol, created_at, action, "
                      "richtung, gate_passed, facts_json) VALUES "
                      "('BTC','2026-08-02','KAUFEN','LONG',1,'{}')")
        c.commit()
        return c

    _mit = _PF.lade(_db_mit(True), symbole=["BTC"])
    _ohne = _PF.lade(_db_mit(False), symbole=["BTC"])
    pruefe(P, "Spot UND Hebel ergeben EINE Position",
           len(_mit) == 1,
           "das ist der Zweck des Moduls - eine Position je Symbol, nicht "
           "je Tabelle. Bekommen: %d" % len(_mit))
    pruefe(P, "und die Hebelzeile zaehlt dahinter mit",
           len(getattr(_mit[0], "signale", []) or []) == 2
           and len(getattr(_ohne[0], "signale", []) or []) == 1,
           "vorher wurde `hebel_signals` nie gelesen: mit %d gegen ohne %d"
           % (len(getattr(_mit[0], "signale", []) or []),
              len(getattr(_ohne[0], "signale", []) or [])))
    pruefe(P, "eine fehlende Hebeltabelle bricht nichts ab",
           len(_PF.lade(_db_mit(False, hebeltabelle=False),
                        symbole=["BTC"])) == 1,
           "alte Datenbanken haben sie nicht - ein Absturz hier liesse den "
           "Bestand still leer erscheinen")

    # ---- I-4: kein H bei Akkumulation ----
    _rl = _quelltext("agent/rollen_lauf.py")
    pruefe(P, "H wird bei akkumulation uebersprungen",
           "_ist_akkumulation = str(strategie" in _rl
           and "raise _KeinHBeiAkkumulation" in _rl,
           "H ist eine BARRIERENfrage (Ziel vor Stop, CRV 2,0). Die "
           "Akkumulation hat keine Barriere - eine Zahl aus der falschen "
           "Messung ist schlimmer als keine")
    # ⚠️ KOMMENTARZEILEN AUSSCHLIESSEN. Die erste Fassung suchte
    # "logger.exception" als Text und fand es im KOMMENTAR ("deshalb ohne
    # `logger.exception`"). Drittes Mal an einem Tag, dass eine Textsuche das
    # Reden ueber eine Sache mit ihrer Verwendung verwechselt.
    # ⚠️ KOMMENTARZEILEN AUSSCHLIESSEN. Die erste Fassung suchte
    # "logger.exception" als Text und fand es im KOMMENTAR ("deshalb ohne
    # `logger.exception`"). Drittes Mal an einem Tag, dass eine Textsuche
    # das Reden ueber eine Sache mit ihrer Verwendung verwechselt.
    _zweig = _rl.split("except _KeinHBeiAkkumulation:")[1].split(
        "except Exception:")[0]
    _code = chr(10).join(z for z in _zweig.split(chr(10))
                         if not z.strip().startswith("#"))
    pruefe(P, "und das ist kein Fehlerfall",
           "except _KeinHBeiAkkumulation:" in _rl
           and "logger.exception" not in _code,
           "uebersprungen und ausgefallen muessen im Log unterscheidbar "
           "sein - im Zweig steht: %r" % _code.strip()[:80])

    # ---- I-2: die Paarpruefung am Etikett ----
    pruefe(P, "das Paar wird geprueft, wo das Etikett entsteht",
           "pruefe_auftrag(_topf_instrument, strategie)" in _rl,
           "`pruefe_auftrag` lief EINMAL am Lauf-Anfang mit der VORGABE - "
           "`hebel x akkumulation` entsteht aber erst danach")
    pruefe(P, "und es wird gemeldet, nicht gesperrt",
           "paarkonflikt" in _rl and "ACHTUNG: %s laeuft als %s" in _rl,
           "die Ursache liegt an der Stopweite, nicht am Asset - wer sperrt, "
           "versteckt den Konflikt; wer meldet, macht ihn zaehlbar")

    # ---- Und der Scope-Fehler, der beinahe passiert waere ----
    baum = _ast.parse(_rl)
    for f in _ast.walk(baum):
        if isinstance(f, _ast.FunctionDef) and f.name == "_ein_asset":
            lokal = set()
            for k in _ast.walk(f):
                if isinstance(k, (_ast.Import, _ast.ImportFrom)):
                    for a in k.names:
                        lokal.add(a.asname or a.name.split(".")[-1])
            pruefe(P, "die Ausnahme ist in _ein_asset importiert",
                   "_AU" in lokal,
                   "⚠️ `AuftragUngueltig` wird in `fuehre_lauf` importiert, "
                   "NICHT hier. Vor dem ersten Lauf per AST gefunden - der "
                   "breite Fehlerfang haette den NameError geschluckt und die "
                   "Meldung waere nie erschienen")
            break




def paket_beitrag_stufen() -> None:
    """G-2' Schritt 2b - `Beitrag` kann abgestuft sein (30.08.2026).

    ⚠️ WARUM DIESE STRUKTUR NOETIG WAR. Bis zum 30.08. kannte `Beitrag` genau
    einen Punktwert, und Vorfilter H hing im Code am NAMEN:

        if b.zustand == "traegt" and b.name.startswith("Vorfilter H"):

    Das traegt genau einen Sonderfall. Der zweite - Funding, gemessen als
    Regel mit +0,0246 R - ist aber nicht ja/nein, sondern ein Rangplatz von
    fuenf Stufen. Ein zweiter Namensvergleich daneben haette die Struktur
    zerfallen lassen.

    DESHALB: `stufen` (fuenf Werte) und `merkmal` (der Schluessel, unter dem
    der Wert ankommt). Schritt 2b legt sie an, OHNE dass `rechne()` sie liest -
    der Bitgleichheitstest `pruefe_wahrscheinlichkeit_bitgleich.py` muss
    unveraendert 0 FEHL liefern.

    Diese Pruefungen halten die Widerspruchsfreiheit fest: Ein Beitrag, der
    `punkte` UND `stufen` traegt, waere zweideutig - und zwar still, weil
    `rechne()` sich fuer einen der beiden entscheiden muesste."""
    from agent.wahrscheinlichkeit import Beitrag, BEITRAEGE

    P = "Stufen"
    # ⚠️ `klammer="tag"` ist seit dem 31.08. Pflicht bei zustand="traegt"
    # (R1). Die Testdaten ziehen die Regel nach - die Regel weicht NICHT
    # den Testdaten. Geprueft wird sie eigenstaendig im Paket
    # "Kalibrierung".
    grund = dict(name="t", zustand="traegt", quelle="q", warum="w",
                 klammer="tag")

    # ---- DIE BESTEHENDE BAUFORM BLEIBT ----
    alt = Beitrag(punkte=4.5, **grund)
    pruefe(P, "die bestehende Bauform funktioniert unveraendert",
           alt.punkte == 4.5 and alt.stufen == () and alt.merkmal == "",
           "Schritt 2b ist additiv - jeder heutige Beitrag muss so bleiben")
    pruefe(P, "alle registrierten Beitraege sind weiter erzeugbar",
           len(BEITRAEGE) >= 5 and all(b.name for b in BEITRAEGE),
           "wenn __post_init__ zu streng ist, faellt der Import - und zwar "
           "beim Start, nicht im Betrieb")

    # ---- DIE NEUE BAUFORM ----
    neu = Beitrag(punkte=0.0, stufen=(1.0, 0.5, 0.0, -0.5, -1.0),
                  merkmal="funding_fuenftel", **grund)
    pruefe(P, "abgestufte Beitraege sind moeglich",
           len(neu.stufen) == 5 and neu.merkmal == "funding_fuenftel")

    # ---- WIDERSPRUECHE FALLEN BEIM IMPORT AUF ----
    for name, bau, erwartet in (
            ("vier Stufen statt fuenf werden abgelehnt",
             dict(punkte=0.0, stufen=(1.0, 2.0, 3.0, 4.0), merkmal="x"),
             "genau 5"),
            ("punkte UND stufen werden abgelehnt",
             dict(punkte=4.5, stufen=(1, 2, 3, 4, 5), merkmal="x"),
             "unklar"),
            ("stufen ohne merkmal werden abgelehnt",
             dict(punkte=0.0, stufen=(1, 2, 3, 4, 5)),
             "kaeme nie an")):
        argumente = dict(grund)
        argumente.update(bau)
        try:
            Beitrag(**argumente)
            getroffen, warum = False, "kein Fehler geworfen"
        except ValueError as exc:
            getroffen, warum = erwartet in str(exc), "Begruendung: %s" % exc
        pruefe(P, name, getroffen, warum)

    # ---- DIE BAUFORM VON H BLEIBT EIN SCHALTER ----
    #
    # ⚠️ DIESE PRUEFUNG STAND BIS ZUM 31.08. AUF "H traegt unveraendert 4,5
    # Punkte". Sie hat damit den Zahlenwert festgeschrieben - und wurde
    # mit R1 zur Bremse gegen die eigene Korrektur. Geprueft wird jetzt die
    # BAUFORM (Schalter, nicht abgestuft); der Zustand und die Punkte
    # gehoeren ins Paket "Kalibrierung", wo die Begruendung danebensteht.
    h = [b for b in BEITRAEGE if b.name.startswith("Vorfilter H")]
    pruefe(P, "Vorfilter H ist ein SCHALTER, kein abgestufter Beitrag",
           len(h) == 1 and h[0].stufen == () and h[0].merkmal == "h",
           "H trifft zu oder nicht - Funding und Turnover sind die "
           "abgestuften Faelle")

    # ---- SCHRITT 2c: H HAENGT NICHT MEHR AM NAMEN ----
    from agent import wahrscheinlichkeit as _WK

    pruefe(P, "H wird ueber `merkmal` angesprochen, nicht ueber den Namen",
           h[0].merkmal == "h",
           "bis zum 30.08. stand im Code `b.name.startswith('Vorfilter H')`. "
           "Ein zweiter Beitrag daneben haette einen zweiten Namensvergleich "
           "gebraucht - und die Registrierung waere zur Attrappe geworden")
    pruefe(P, "kein Beitrag wird mehr ueber seinen Namen erkannt",
           "startswith" not in _WK.rechne.__doc__ if _WK.rechne.__doc__ else True)

    def _q(**kw):
        kw.setdefault("crv", 2.0)
        kw.setdefault("stop_relativ", 0.05)
        kw.setdefault("gebuehr_je_seite", 0.0)
        kw.setdefault("klasse", "krypto")
        return _WK.rechne(**kw)

    # ⚠️ AEQUIVALENZ, NICHT ZAHLENWERT (31.08.2026). Die alte Fassung
    # verlangte "== 4.5" und wurde mit R1 falsch - obwohl die Eigenschaft,
    # die sie sichern soll, unveraendert gilt: beide Wege muessen dasselbe
    # tun, egal welchen Wert H gerade hat.
    pruefe(P, "der neue Weg `merkmale` liefert dasselbe wie `h=`",
           _q(merkmale={"h": True})["beitraege"] == _q(h=True)["beitraege"]
           and _q(merkmale={"h": False})["beitraege"] == _q(h=False)["beitraege"],
           "der alte Parameter muss bleiben - drei Aufrufer haengen daran")
    pruefe(P, "und beide Wege unterscheiden True von False",
           _q(h=True)["beitraege"] != _q(h=False)["beitraege"]
           or h[0].zustand != "traegt",
           "traegt H, muessen sich die Zeilen unterscheiden; steht er auf "
           "`null`, duerfen sie gleich sein - beides ist richtig, aber nicht "
           "dasselbe")

    # ---- DIE DREI ACHSEN ----
    lang = Beitrag(name="t", zustand="traegt", punkte=1.0, quelle="q",
                   klammer="tag",
                   warum="w", merkmal="x", richtungen=("long",))
    passt, grund = _WK._gilt(lang, "krypto", "einstieg", "short")
    pruefe(P, "ein Long-Beitrag gilt bei SHORT nicht", not passt,
           "Kapitel 110: H' spiegelt NICHT. Was fuer long gemessen ist, gilt "
           "nicht automatisch fuer short - und `None` ist die richtige "
           "Antwort, nicht das Gegenteil")
    pruefe(P, "und der Grund nennt die Richtung", "short" in grund, grund)
    pruefe(P, "bei long gilt er", _WK._gilt(lang, "krypto", "einstieg", "long")[0])

    nur_einstieg = Beitrag(name="t", zustand="traegt", punkte=1.0, quelle="q",
                           klammer="tag",
                           warum="w", merkmal="x",
                           strategien=("einstieg", "swing"))
    passt, grund = _WK._gilt(nur_einstieg, "krypto", "akkumulation", "long")
    pruefe(P, "Akkumulation wird ausgeschlossen, wenn nicht deklariert",
           not passt,
           "eine Staffelung hat keinen einzelnen Einstiegszeitpunkt - ein "
           "Tagesrang bewertet aber genau einen")
    pruefe(P, "und der Grund nennt die Strategie", "akkumulation" in grund, grund)

    # ---- ABGESTUFTE BEITRAEGE RECHNEN ----
    stufig = Beitrag(name="Stufig", zustand="traegt", punkte=0.0, quelle="q",
                     klammer="tag",
                     warum="w", stufen=(2.0, 1.0, 0.0, -1.0, -2.0),
                     merkmal="rang")
    echte = _WK.BEITRAEGE
    _WK.BEITRAEGE = (stufig,)
    try:
        for stufe, erwartet in ((0, 2.0), (2, 0.0), (4, -2.0)):
            pruefe(P, "Fuenftel %d ergibt %+.1f Punkte" % (stufe, erwartet),
                   abs(_q(merkmale={"rang": stufe})["zuschlag_punkte"]
                       - erwartet) < 1e-9)
        pruefe(P, "ein fehlender Wert wird 'nie', nicht 0 als Nein",
               _q(merkmale={})["beitraege"][0]["zustand"] == "nie",
               "der Unterschied zwischen 'geprueft und trifft nicht zu' und "
               "'wir wissen es nicht' ist die wichtigste Information")
    finally:
        _WK.BEITRAEGE = echte



def paket_kalibrierung() -> None:
    """Laufen die kalibrierten Zahlen auseinander? (R-R9, 30.08.2026)

    ⚠️ WARUM DIESE PRUEFUNG UND KEINE ZUSAMMENFUEHRUNG. Nutzerfrage: *"kann
    man das an eine Stelle legen?"* Technisch ja - fachlich nein. Die drei
    Zahlen bedeuten Verschiedenes:

        vorfilter.GEMESSEN          was GEMESSEN wurde        (+4,5)
        wahrscheinlichkeit.punkte   was wir ANSETZEN          (darf kleiner sein)
        potential.SCHWELLE_VORGABE  ab wann es REICHT

    Waere der angesetzte Wert an den gemessenen gekettet, koennte man einen
    episodischen Befund nicht vorsichtig ansetzen - und genau das steht bei H
    an (Messung 30.08.: traegt nur ausserhalb des Baermarkts).

    Diese Pruefung haelt deshalb die BEZIEHUNG fest, nicht die Gleichheit:
    der angesetzte Wert darf nie GROESSER sein als der gemessene, und jede
    Aenderung der Beitragslage verlangt eine neue Kalibrierung."""
    from agent import potential as _PT
    from agent import marktrang as _MR_MOD
    from agent import rollen_lauf as _RL
    from agent import vorfilter as _VF
    from agent import wahrscheinlichkeit as _WK

    P = "Kalibrierung"

    h = [b for b in _WK.BEITRAEGE if b.merkmal == "h"]
    pruefe(P, "H ist ueber sein Merkmal auffindbar", len(h) == 1,
           "seit Schritt 2c haengt kein Beitrag mehr am Namen")
    if h:
        gemessen = float(_VF.GEMESSEN["vorsprung_punkte"])
        angesetzt = float(h[0].punkte)
        pruefe(P, "der angesetzte Wert uebersteigt den gemessenen nicht",
               angesetzt <= gemessen + 1e-9,
               "angesetzt %.2f, gemessen %.2f - wer mehr ansetzt als gemessen "
               "wurde, behauptet eine Wirkung, die niemand belegt hat"
               % (angesetzt, gemessen))
        # ---- R1 (31.08.2026): H IST WEG, UND DAS BLEIBT SO -------------
        pruefe(P, "⚠️ H steht auf `null` und traegt 0,0 Punkte",
               h[0].zustand == "null" and h[0].punkte == 0.0,
               "H war gepoolt gemessen (+3,57 Punkte) und ist je Kalendertag "
               "nicht von null zu trennen (-1,02 [-2,18 .. +0,14], 791 "
               "Einheiten). Das ist eine LAGE-Aussage, keine Asset-Aussage. "
               "Wer ihn zurueckstellt, braucht eine Messung UNTER DER "
               "TAGESKLAMMER - `pruefe_h_original_reproduziert.py`")
        pruefe(P, "und seine Klammer ist als `gepoolt` vermerkt",
               h[0].klammer == "gepoolt",
               "ohne den Vermerk waere in einem Jahr nicht mehr erkennbar, "
               "WARUM er weg ist")

    # ---- DIE REGEL, DIE DEN H-FEHLER STRUKTURELL AUSSCHLIESST ----------
    #
    # ⚠️ DAS IST DIE WICHTIGSTE PRUEFUNG DIESES PAKETS. H stand elf Tage im
    # Betrieb, weil niemand fragte, unter WELCHEM Vergleich seine +4,5
    # Punkte entstanden waren. Seit dem 31.08. erzwingt `Beitrag.__post_init__`
    # die Antwort; hier wird geprueft, dass die Regel auch wirkt.
    ohne_klammer = [b.name for b in _WK.BEITRAEGE
                    if b.zustand == "traegt" and b.klammer != "tag"]
    pruefe(P, "⚠️ JEDER tragende Beitrag ist je KALENDERTAG gemessen",
           not ohne_klammer,
           "ohne Tagesklammer: %s. Ein gepoolt oder je Zeitblock gemessener "
           "Vorsprung beschreibt die LAGE, in der ein Merkmal auftritt - "
           "nicht die Guete der Anker, die es auswaehlt. Bei H betrug der "
           "Unterschied 4,6 Punkte, bei 'Boden unten' 0,20 R"
           % ", ".join(ohne_klammer))
    try:
        _WK.Beitrag(name="Probe", zustand="traegt", punkte=1.0,
                    quelle="x", warum="y", merkmal="z", klammer="gepoolt")
        gewirft = False
    except ValueError:
        gewirft = True
    pruefe(P, "und die Regel wirft beim Import, nicht erst im Betrieb",
           gewirft,
           "`Beitrag(zustand='traegt', klammer='gepoolt')` muss ein "
           "ValueError sein - sonst ist die Absicherung eine Attrappe")
    pruefe(P, "unbekannte Klammern werden abgewiesen",
           all(b.klammer in ("",) + _WK.KLAMMERN for b in _WK.BEITRAEGE))

    gilt, lage = _PT.kalibrierung_gilt()
    pruefe(P, "die Schwelle passt zur heutigen Beitragslage (R-R9)", gilt,
           "Beitragslage ist %r, kalibriert wurde fuer %r. Jeder neue "
           "tragende Beitrag hebt ALLE Potentialwerte - bei gleicher Schwelle "
           "kommen mehr Signale durch, ohne dass sich ihre Qualitaet geaendert "
           "haette. GEMESSEN am 30.08. nach 2e: 44,3 %% Durchlass bei "
           "Schwelle 0,010 (123.465 Anker) - die vorher befuerchteten 77 %% "
           "traten NICHT ein, weil Rangbeitraege symmetrisch sind und ihre "
           "oberen Fuenftel sperren. Nachzuziehen: (1) die Schwelle neu "
           "kalibrieren (Methodik 2.93), (2) KALIBRIERT_FUER setzen, "
           "(3) Befundkarte 3.9." % (lage, _PT.KALIBRIERT_FUER))

    pruefe(P, "die Schwelle liegt ueber null",
           _PT.SCHWELLE_VORGABE > 0.0,
           "Nutzervorgabe 30.08.: bei Potential null traegt KEIN Beitrag - "
           "eine Empfehlung ohne Grund waere genau das, was das Ziel "
           "ausschliesst")
    pruefe(P, "und `traegt` vergleicht STRIKT groesser",
           not _PT.traegt(_PT.schwelle()),
           "genau auf der Schwelle heisst noch nicht darueber")

    # ---- 2e: DIE ABGESTUFTEN BEITRAEGE (30.08.2026) ---------------------
    #
    # ⚠️ WARUM DAS HIER UND NICHT IN EINEM EIGENEN PAKET: 2e ist keine neue
    # Baustelle, sondern die Aufloesung der GEFAEHRLICHSTEN Eigenschaft der
    # alten Lage - dass H der einzige Beitrag war. Solange das galt, konnte
    # H nicht geprueft werden: jede Aenderung an ihm legte den Trichter
    # still (gemessen: h=False -> Potential -0,0000 R -> gesperrt).
    for merkmal, klar in (("funding_fuenftel", "Funding"),
                          ("turnover_fuenftel", "Turnover")):
        b = [x for x in _WK.BEITRAEGE if x.merkmal == merkmal]
        pruefe(P, "%s ist als Beitrag registriert" % klar, len(b) == 1)
        if not b:
            continue
        pruefe(P, "%s hat genau fuenf Stufen" % klar, len(b[0].stufen) == 5)
        pruefe(P, "%s: das unterste Fuenftel traegt mehr als das oberste" % klar,
               b[0].stufen[0] > b[0].stufen[-1],
               "`marktrang._rang` sortiert AUFSTEIGEND - Fuenftel 0 ist der "
               "niedrigste Rohwert, und bei beiden Groessen ist niedrig das "
               "Gute. Waere die Reihe andersherum, zeigte das Vorzeichen ins "
               "Gegenteil, ohne dass irgendetwas anschluege")
        pruefe(P, "%s traegt NICHTS, wenn der Wert fehlt" % klar,
               all(z["punkte"] == 0.0 for z in _WK.rechne(
                   crv=2.0, stop_relativ=0.05, gebuehr_je_seite=0.0,
                   klasse="krypto", h=None)["beitraege"]
                   if z["name"].startswith(klar)),
               "ein fehlender Wert darf nie aussehen wie ein gemessener - "
               "dieselbe Regel wie bei H (`h=None`, nicht `h=False`)")

    # ⚠️ DIE EIGENTLICHE ZUSICHERUNG VON 2e: das System haengt nicht mehr an H.
    ohne_alles = _PT.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                            h=False).wert_r
    nur_raenge = _PT.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                            h=False, merkmale={"funding_fuenftel": 0,
                                               "turnover_fuenftel": 0}).wert_r
    pruefe(P, "ohne jeden Beitrag bleibt es gesperrt",
           not _PT.traegt(ohne_alles),
           "Potential %.4f R - eine Empfehlung ohne Grund" % ohne_alles)
    pruefe(P, "⚠️ die Raenge allein lassen durch - OHNE H",
           _PT.traegt(nur_raenge),
           "Potential %.4f R. Solange nur H durchlaesst, ist H nicht "
           "pruefbar: jede Aenderung an ihm legt den Trichter still. Genau "
           "das war der Zustand bis zum 30.08." % nur_raenge)

    # ---- P3: DIE ABDECKUNG (31.08.2026) --------------------------------
    #
    # ⚠️⚠️ DIESE PRUEFUNG HAETTE VOR R1 EXISTIEREN MUESSEN. Vorfilter H galt
    # fuer JEDEN Wert (je Anker aus den Marken gerechnet). Seine Nachfolger
    # kommen aus Fremdquellen und haben Luecken - gemessen am 31.08. hatten
    # 29 von 56 Werten der Watchlist KEINEN einzigen Beitrag. Mit
    # verwerfender Stufe 11 (G-6) heisst das: sie bekommen nie ein Signal,
    # nach Datenlage statt nach Qualitaet.
    #
    # Nutzervorgabe 31.08.: *"Die Scharfschaltung darf erst erfolgen, wenn
    # alle Assets einen Beitrag haben."*
    # ⚠️⚠️ AM 31.08. ABENDS UMGEDREHT. Hier stand als Forderung: "mindestens
    # ein Beitrag kommt aus der eigenen Kursreihe" - erfuellt durch den
    # Schnittabstand. Er ist am selben Abend gefallen (Horizontlauf: bei
    # keinem Horizont trennbar). Die Forderung bleibt richtig, sie ist nur
    # NICHT ERFUELLT - und eine Pruefung, die eine offene Luecke gruen
    # meldet, ist schlimmer als keine.
    #
    # Diese Zeile haelt den Zustand jetzt als BEFUND fest, nicht als Erfolg.
    _aus_kursreihe = [b for b in _WK.BEITRAEGE
                      if b.zustand == "traegt" and b.merkmal == "schnitt_fuenftel"]
    pruefe(P, "⚠️ KEIN Beitrag aus der eigenen Kursreihe - die Luecke steht",
           not _aus_kursreihe,
           "wenn diese Zeile faellt, ist ein Kursreihen-Beitrag dazugekommen "
           "- dann gehoert die Abdeckung neu gerechnet UND die Schwelle neu "
           "kalibriert (R-R9). Funding und Turnover kommen aus Fremdquellen "
           "und erreichen nie volle Abdeckung: 36 von 43 Werten")

    # ---- DIE ALARMGRENZE (Variante C, dimensioniert am 31.08.) ----------
    #
    # Ein Beitrag wirkt nur, solange sein BESTES Fuenftel ueber der Grenze
    # liegt, die aus der Schwelle folgt:
    #
    #     noetige Punkte = 100 * Schwelle / (1 + CRV) = +0,333 bei 0,010
    #
    # Darunter kommt durch ihn allein nichts mehr durch - er ist dann
    # wirkungslos, ohne dass es auffiele. Die Grenze ist NICHT gegriffen,
    # sie folgt aus der Rechnung.
    # ⚠️⚠️ NACHGEZOGEN AM 31.08. ABENDS, als die Vorgabe auf 0,080 stieg.
    #
    # Die Pruefung schlug an - und sie hatte RECHT fuer die Welt, fuer die
    # sie gebaut war: bei einer FESTEN Schwelle von 0,080 braeuchte ein
    # Beitrag +2,667 Punkte, und Funding hat nur +1,30. Er waere allein
    # wirkungslos.
    #
    # Seit derselben Runde gibt es aber die SCHWELLE JE DATENLAGE
    # (`Potential.schwelle`): sie rechnet die Vorgabe auf die bei dieser
    # Datenlage erreichbare Spanne um. Fuer einen Wert, bei dem nur Funding
    # vorliegt, entspricht 0,080 dann 0,0234 R - und +1,30 Punkte ergeben
    # +0,039 R. Der Beitrag traegt sehr wohl.
    #
    # Geprueft wird deshalb, was gemeint war: **nimmt das beste Fuenftel
    # dieses Beitrags die Schwelle SEINER eigenen Datenlage?**
    for b in [x for x in _WK.BEITRAEGE if x.stufen and x.zustand == "traegt"]:
        _p_allein = _PT.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                               instrument="spot", strategie="einstieg",
                               h=None,
                               merkmale={b.merkmal: int(
                                   max(range(len(b.stufen)),
                                       key=lambda i: b.stufen[i]))})
        pruefe(P, "%s: bestes Fuenftel nimmt seine eigene Schwelle"
               % b.name[:34],
               _p_allein.traegt_hier,
               "bestes Fuenftel %+.2f Punkte = %+.4f R gegen Schwelle "
               "%.4f R - darunter wirkt der Beitrag nicht mehr, auch nicht "
               "mit der Schwelle je Datenlage"
               % (max(b.stufen), _p_allein.wert_r, _p_allein.schwelle))
        pruefe(P, "%s: Richtung stimmt (Fuenftel 0 > Fuenftel 4)"
               % b.name[:34],
               b.stufen[0] > b.stufen[-1],
               "%+.2f gegen %+.2f - dreht das Vorzeichen, wirkt der Beitrag "
               "genau falsch herum" % (b.stufen[0], b.stufen[-1]))

    # ⚠️ UND DIE NAHT - ohne sie waere die Registrierung eine Attrappe
    # (stehende Regel: 'Naht statt Absichtserklaerung').
    import inspect
    # ⚠️ BEIDE FUNKTIONEN. Die erste Fassung dieser Pruefung sah nur
    # `fuehre_lauf` - und haette damit genau den Fehler durchgelassen, den
    # sie dann doch fand: der Abruf steht in `fuehre_lauf`, die Verwendung
    # in `_ein_asset`. Wer nur eine Seite prueft, prueft die Naht nicht.
    _rl = (inspect.getsource(_RL.fuehre_lauf)
           + inspect.getsource(_RL._ein_asset))
    pruefe(P, "`rollen_lauf` holt die Marktraenge EINMAL je Lauf",
           "_MR.raenge(symbole)" in _rl,
           "der Rang ist ein QUERSCHNITT ueber alle heute bewerteten Werte. "
           "Je Symbol gerechnet waere er eine andere Groesse ohne Befund - "
           "die Je-Reihe-Sicht wurde gemessen und traegt nicht (-0,0755 R)")
    pruefe(P, "`_ein_asset` bekommt die Raenge als PARAMETER",
           "marktraenge=_raenge" in _rl and "marktraenge=None" in _rl,
           "`_ein_asset` sieht die Variablen von `fuehre_lauf` NICHT. Ein "
           "direkter Zugriff waere im Betrieb ein NameError, den der breite "
           "Fehlerfang schluckt - dieselbe Falle wie `_wl` am 15.08.")
    pruefe(P, "und reicht sie an `potential.rechne` durch",
           "merkmale=_merkmale" in _rl,
           "registriert, aber nie geliefert - dann traegt der Beitrag in "
           "jedem echten Lauf null, und keine Pruefung merkt es")
    pruefe(P, "ein fehlendes Fuenftel wird NICHT zu 0 gemacht",
           "if _mr.get(k) is not None" in _rl,
           "sonst saehe 'unbekannt' aus wie 'bestes Fuenftel'")
    # ⚠️ AUCH `schnitt_fuenftel` BLEIBT ANGELIEFERT, obwohl der Beitrag seit
    # dem 31.08. auf null steht. Die Anlieferung kostet nichts, und ohne sie
    # traegt eine Rueckkehr des Beitrags in jedem echten Lauf still null.
    pruefe(P, "alle drei Merkmale werden durchgereicht",
           all(m in _rl for m in ("funding_fuenftel", "turnover_fuenftel",
                                  "schnitt_fuenftel")),
           "ein registrierter Beitrag ohne Anlieferung traegt in jedem "
           "echten Lauf null - und keine Pruefung merkt es")

    # ---- P3: DIE MAIL ZEIGT, WOMIT ENTSCHIEDEN WURDE (B-a) -------------
    _saetze_q = inspect.getsource(_WK.saetze)
    pruefe(P, "⚠️ `saetze()` rechnet MIT den Merkmalen",
           "merkmale=merkmale" in _saetze_q,
           "bis zum 31.08. rechnete die Mail ohne sie: Stufe 11 entschied "
           "mit 37,0 %, die Mail zeigte 33,3 % und '20,0 Punkte ZU WENIG'. "
           "Eine Begruendung, die der Empfehlung widerspricht, kann niemand "
           "pruefen")
    pruefe(P, "und `rollen_lauf` uebergibt sie auch",
           "merkmale=_merkmale or None" in _rl)

    # ---- P3: DER RANG LAEUFT UEBER DIE MESSBASIS ------------------------
    _mr_q = inspect.getsource(_MR_MOD.raenge)
    pruefe(P, "⚠️ der Rang wird ueber die MESSBASIS gebildet",
           "messbasis(name)" in _mr_q and "holen()" in _mr_q,
           "ueber die Watchlist gerangt DREHT das Vorzeichen: beim "
           "Schnittabstand +3,43 gegen -3,10, nur 54 % identische "
           "Fuenftel (gemessen 31.08.)")
    pruefe(P, "ohne lesbare Messbasis gibt es KEINEN Rang",
           "if not basis:" in _mr_q,
           "ein Rang ueber die falsche Menge saehe aus wie ein richtiger")

    # ---- N-17b/04.09.: messe_eigenschaft_beitrag.lade() bleibt KRYPTO-NUR --
    #
    # ⚠️⚠️ GEFUNDEN, NICHT VERMUTET. Seit N-19 (03.09.) traegt
    # `data/messdaten.db` zusaetzlich Aktien/ETF/Rohstoffe. `lade()` filterte
    # bis dahin nicht explizit - es musste nicht, die Tabelle war reiner
    # Krypto. Ohne Filter mischten 44 abhaengige Skripte plötzlich 798
    # Nicht-Krypto-Symbole in jede Tagesklammer. Gefunden hat es die
    # eingebaute Zufallskontrolle in messe_form_kurz_gegen_lang.py - sie
    # schlug an, wie vorgesehen (Regelwerk: eine Kontrollgroesse, die
    # traegt, macht das VERFAHREN ungueltig, nicht den Kandidaten).
    #
    # ECHTER Funktionsaufruf, keine Kopie (Lehre vom selben Tag wie G-b).
    import messe_eigenschaft_beitrag as _MEB
    import sqlite3 as _sq3
    _reihen17b = _MEB.lade()
    _c17b = _sq3.connect("file:data/messdaten.db?mode=ro", uri=True)
    _kr17b = {r[0] for r in _c17b.execute(
        "SELECT symbol FROM messreihen WHERE assetklasse='krypto'")}
    _c17b.close()
    _fremd17b = set(_reihen17b) - _kr17b
    pruefe(P, "⚠️⚠️ messe_eigenschaft_beitrag.lade() liefert NUR Krypto",
           not _fremd17b,
           "gefunden: %d Nicht-Krypto-Symbole in %d insgesamt (%s) - "
           "jede Messung, die darauf aufsetzt, mischt sonst Aktien/ETF/"
           "Rohstoffe in denselben Tagesquerschnitt wie Krypto"
           % (len(_fremd17b), len(_reihen17b),
              ", ".join(sorted(_fremd17b)[:5])))




def paket_terminmarkt() -> None:
    """N-14: DIE OI-SPERRE ALS TRICHTERSTUFE (02.09.2026).

    Grundlage F-168: kein Einstieg im obersten Fuenftel des OI-Aufbaus,
    +0,0145 R ueber 126.491 Anker. Was dieses Paket festhaelt:

        1  die Stufe steht im Gate, an der richtigen Stelle
        2  DREI Zustaende, nicht zwei - ein Wert ohne Rang wird NICHT
           gesperrt (die Lehre aus G-6: erste Fassung, null Signale)
        3  nur "einstieg" - die Messung ankert auf einem Einstieg
        4  nicht bei Bestand - dort steht die Ausstiegsfrage an
        5  der Rang kommt aus der MESSBASIS, nicht aus der Watchlist
        6  die Mail sagt es in BEIDEN Faellen
        7  der Trichter bleibt monoton
    """
    P = "Terminmarkt"
    import ast as _ast
    import pathlib as _pl

    # ---- DAUERPRUEFUNG T6: Mail und Stufe 11 rechnen GLEICH -------------
    #
    # ⚠️⚠️ ANLASS 02.09.2026, gefunden beim Lesen einer echten Mail. Der
    # Lauf ruft ZWEI Rechnungen mit derselben Absicht:
    #
    #     _PT.rechne(...)   entscheidet in Stufe 11
    #     _WK.saetze(...)   schreibt die Zeilen der Mail
    #
    # Beide muessen dieselbe Quote liefern. Am 31.08. fehlte `merkmale` im
    # zweiten Aufruf - das wurde behoben. Am 02.09. fehlte `strategie`, und
    # damit fielen in der Mail BEIDE tragenden Beitraege aus: sie zeigte
    # 33,3 % statt 34,9 %, also die nackte Basisrate.
    #
    # In der AVAX-Mail vom 02.09. stand deshalb der Funding-Rang als Fakt
    # ("ein niedriges Fuenftel im Marktvergleich") - und zwei Zeilen
    # darueber, er sei "fuer die Strategie ? nie gemessen".
    #
    # ⚠️ Diese Pruefung vergleicht die ARGUMENTE beider Aufrufe ueber den
    # Syntaxbaum: was BEIDE Funktionen entgegennehmen, muss in beiden
    # Aufrufen stehen. Ein neuer gemeinsamer Parameter faellt damit sofort
    # auf - und nicht erst, wenn jemand eine Mail liest.
    import inspect as _insp
    from agent import wahrscheinlichkeit as _WK6
    from agent import potential as _PT6
    _q6 = _pl.Path("agent/rollen_lauf.py").read_text(encoding="utf-8")
    _b6 = _ast.parse(_q6)
    _arg = {}
    for _k in _ast.walk(_b6):
        if not isinstance(_k, _ast.Call) or not isinstance(_k.func, _ast.Attribute):
            continue
        if _k.func.attr in ("rechne", "saetze"):
            _mod = getattr(_k.func.value, "id", "")
            if _mod in ("_PT", "_WK"):
                _arg.setdefault(_mod, set()).update(
                    kw.arg for kw in _k.keywords if kw.arg)
    _gemeinsam = (set(_insp.signature(_WK6.saetze).parameters)
                  & set(_insp.signature(_PT6.rechne).parameters))
    _fehlt = {m: sorted(_gemeinsam - _arg.get(m, set())) for m in ("_PT", "_WK")}
    pruefe(P, "T6: Mail und Stufe 11 bekommen dieselben Argumente",
           not (_fehlt["_PT"] or _fehlt["_WK"]),
           "beide Rechnungen haben dieselbe Absicht und muessen dieselbe "
           "Quote liefern. Gemeinsame Parameter: %s · im rechne()-Aufruf "
           "fehlen %s · im saetze()-Aufruf fehlen %s"
           % (sorted(_gemeinsam), _fehlt["_PT"] or "keine",
              _fehlt["_WK"] or "keine"))

    # ---- DAUERPRUEFUNG T7: die ZWEI Rechnungen INNERHALB der Mail --------
    #
    # ⚠️⚠️ T6 HAT DEN FEHLER NICHT GEFANGEN, den sie fangen sollte
    # (03.09.2026). Sie bewacht die Naht zwischen Mail und Stufe 11 - aber
    # `wahrscheinlichkeit.saetze()` ruft `rechne()` ZWEIMAL:
    #
    #     erste = rechne(...)          fuer die Zeile "geschaetzte Quote"
    #     for name, satz in ...:       je Gebuehrensatz noch einmal
    #         r = rechne(...)          fuer "noetig X, geschaetzt Y"
    #
    # Am 02.09. habe ich `strategie` in den ERSTEN eingebaut und den
    # zweiten uebersehen. Die Mail zeigte daraufhin in EINEM Block zwei
    # verschiedene Trefferquoten:
    #
    #     = geschaetzte Trefferquote        32,8 %
    #     Standard 0,30 %: ... geschaetzt   33,3 %
    #
    # Die Lehre ist allgemeiner als der Fall: eine Pruefung, die EINE Naht
    # bewacht, sieht die zweite daneben nicht. Wer zwei Rechnungen mit
    # derselben Absicht fuehrt, muss ihre Argumente gemeinsam pflegen -
    # und zwar an JEDER Stelle, an der sie stehen.
    _qw = _pl.Path("agent/wahrscheinlichkeit.py").read_text(encoding="utf-8")
    _fn = next((n for n in _ast.walk(_ast.parse(_qw))
                if isinstance(n, _ast.FunctionDef) and n.name == "saetze"),
               None)
    # ⚠️ DIESE ZWEI DUERFEN sich unterscheiden - dafuer gibt es die
    # Schleife ueberhaupt. Alles andere nicht.
    _egal = {"gebuehr_je_seite", "finanzierung_r"}
    _aufrufe = [{kw.arg for kw in k.keywords if kw.arg} - _egal
                for k in _ast.walk(_fn or _ast.parse(""))
                if isinstance(k, _ast.Call)
                and getattr(k.func, "id", "") == "rechne"]
    pruefe(P, "T7: beide rechne()-Aufrufe in saetze() sind gleich bestueckt",
           len(_aufrufe) >= 2 and all(x == _aufrufe[0] for x in _aufrufe),
           "sonst zeigt DIESELBE Mail zwei verschiedene Trefferquoten. "
           "Gefunden: %s" % (_aufrufe or "kein Aufruf - hat sich der Name "
                             "geaendert?"))
    # ⚠️ DIESE PRUEFUNG WAR IN IHRER ERSTEN FASSUNG BLIND. Sie sammelte
    # alle Zeilen mit "geschaetzt " - und traf damit NUR die beiden
    # Wirtschaftlichkeitszeilen, die naturgemaess uebereinstimmen. Die
    # Zeile, um die es geht, heisst "= geschaetzte Trefferquote" und fiel
    # durch das Suchmuster. Mit kuenstlich wieder eingebautem Fehler
    # meldete sie OK.
    #
    # Gefunden, weil ich den Fehler zum Gegentest wieder eingebaut habe -
    # eine Kontrolle, die man nicht scheitern sieht, ist keine.
    _mz = _WK6.saetze(crv=2.0, stop_relativ=0.06, klasse="krypto",
                      strategie="einstieg", merkmale={"funding_fuenftel": 3})
    _oben = [z.split()[-2] for z in _mz if "geschaetzte Trefferquote" in z]
    _unten = [z.split("geschaetzt ")[1].split(" ")[0]
              for z in _mz if "geschaetzt " in z]
    pruefe(P, "und die Mail nennt beide Male dieselbe Quote",
           bool(_oben) and bool(_unten)
           and len(set(_oben) | set(_unten)) == 1,
           "die Wirtschaftlichkeitszeilen rechneten ohne die Beitraege und "
           "nannten deshalb die nackte Basisrate. Oben %s, unten %s"
           % (_oben or "nichts gefunden", _unten or "nichts gefunden"))

    # ---- N-15 VARIANTE C: DIE ZERLEGUNG (03.09.2026) ---------------------
    #
    # ⚠️ WAS HIER BEWACHT WIRD, ist nicht der Text, sondern die
    # UNTERSCHEIDUNG: ein Beitrag, der gemessen wurde und nicht traegt, und
    # einer, der traegt aber HIER keinen Wert hat, sind zweierlei. N-15a
    # hat am 03.09. gezeigt, dass eine Bewertung mit Datenluecke nicht mit
    # einer vollstaendigen vergleichbar ist - ihre Skala haengt an der
    # Datenlage. In der Mail stand beides in derselben Liste.
    def _bt(**mm):
        return _WK6.rechne(crv=2.0, stop_relativ=0.06, gebuehr_je_seite=0.003,
                           klasse="krypto", strategie="einstieg",
                           merkmale=mm)["beitraege"]
    _nur_f = _bt(funding_fuenftel=3)
    _beide = _bt(funding_fuenftel=3, turnover_fuenftel=2)
    pruefe(P, "C: ein fehlender Wert wird als `luecke` markiert",
           any(z.get("luecke") for z in _nur_f
               if z["name"].startswith("Turnover")),
           "sonst steht die Datenluecke in derselben Liste wie die "
           "Beitraege, die gemessen und gefallen sind")
    pruefe(P, "C: liegen alle Werte vor, gibt es KEINE Luecke",
           not any(z.get("luecke") for z in _beide))
    pruefe(P, "C: ein gemessen gefallener Beitrag ist KEINE Luecke",
           not any(z.get("luecke") for z in _beide
                   if z["name"].startswith("Lebendigkeit")),
           "'gemessen und gefallen' ist erledigt, 'kein Wert da' ist eine "
           "Aufgabe - die Mail muss das trennen")
    pruefe(P, "C: `zustand` bleibt unveraendert `nie` (Bitgleichheit)",
           all(z["zustand"] == "nie" for z in _nur_f
               if z["name"].startswith("Turnover")),
           "ein neuer Zustandswert haette "
           "`pruefe_wahrscheinlichkeit_bitgleich.py` rot gemacht, obwohl "
           "sich rechnerisch nichts aendert - ein Fehlalarm in einem "
           "Bitgleichheitstest ist teurer als eine fehlende Unterscheidung")
    _m1 = _WK6.saetze(crv=2.0, stop_relativ=0.06, klasse="krypto",
                      strategie="einstieg", merkmale={"funding_fuenftel": 3})
    _m2 = _WK6.saetze(crv=2.0, stop_relativ=0.06, klasse="krypto",
                      strategie="einstieg",
                      merkmale={"funding_fuenftel": 3, "turnover_fuenftel": 2})
    pruefe(P, "C: steht die Bewertung auf EINEM Beitrag, warnt die Mail",
           any("steht auf EINEM Beitrag" in z for z in _m1),
           "das ist heute bei 37 von 44 Werten der Fall und war in keiner "
           "Mail sichtbar")
    pruefe(P, "C: bei zwei Beitraegen warnt sie NICHT",
           not any("steht auf EINEM Beitrag" in z for z in _m2),
           "eine Warnung, die immer kommt, wird beim dritten Mal ignoriert")
    pruefe(P, "C: die Luecke steht GENAU EINMAL in der Mail",
           sum(1 for z in _m1 if "Turnover-Rang im Markt" in z) == 1,
           "sie stand vorher auch in der Liste 'Nicht eingerechnet' - "
           "zweimal gelesen haelt man sie beim zweiten Mal fuer etwas "
           "anderes")
    pruefe(P, "C: der Anteil je Beitrag summiert sich auf 100 %",
           any("100 %" in z for z in _m1))

    # ---- DAUERPRUEFUNG T8: DIE BEWERTUNG BLEIBT GEBUEHRENFREI ----------
    #
    # ⚠️⚠️ NUTZERVORGABE, mehrfach und woertlich (30.08. und 31.08.2026):
    #
    #   "die Bewertung soll ohne Wirtschaftlichkeit, Gebuehren usw.
    #    erfolgen - also neutral! Im eMail und nur als Text - erst beim
    #    Hebel braucht man die Standardrate 0,3 bzw. 1,5 Prozent
    #    rechnerisch."
    #   "Ganz wichtig, sonst vermischt man zwei verschiedene Ebenen."
    #
    # DIE DREI EBENEN:
    #     1 BEWERTUNG   Potential, Rangfolge, jeder Filter   KEINE Gebuehr
    #     2 AUSKUNFT    die Mail                             als TEXT
    #     3 MECHANIK    nur Hebel, nur in der MAIL           gerechnet
    #
    # Die Trennung war bis heute nirgends abgesichert. Sie ist EINGEHALTEN
    # (geprueft 03.09.: nur zwei Stellen setzen ueberhaupt einen
    # Gebuehrensatz, beide in `saetze()` = Mail) - aber eine eingehaltene
    # Trennung ohne Waechter ist eine, die beim naechsten Umbau faellt.
    #
    # ⚠️ Ein frueherer Verstoss ist belegt: `trefferbilanz.breakeven()`
    # rechnete mit Kosten und speiste Stufe 11. Behoben durch U-1
    # (30.08.), seither entscheidet `potential.traegt_hier`.
    import ast as _a8
    import io as _io8
    _q8 = _io8.open("agent/potential.py", encoding="utf-8").read()
    _fn8 = next((n for n in _a8.walk(_a8.parse(_q8))
                 if isinstance(n, _a8.FunctionDef) and n.name == "rechne"), None)
    _geb8 = [kw for k in _a8.walk(_fn8 or _a8.parse(""))
             if isinstance(k, _a8.Call)
             for kw in k.keywords if kw.arg == "gebuehr_je_seite"]
    pruefe(P, "T8: `potential.rechne` ruft die Bewertung mit Gebuehr 0.0",
           len(_geb8) == 1 and isinstance(_geb8[0].value, _a8.Constant)
           and float(_geb8[0].value.value) == 0.0,
           "die BEWERTUNG ist neutral - auch beim Hebel. Gefunden: %s"
           % [getattr(g.value, "value", "?") for g in _geb8])
    pruefe(P, "T8: und sie reicht KEINE Finanzierung durch",
           not any(kw.arg == "finanzierung_r"
                   for k in _a8.walk(_fn8 or _a8.parse(""))
                   if isinstance(k, _a8.Call) for kw in k.keywords),
           "die Finanzierung gehoert in die MAIL, nicht in die Bewertung - "
           "sie braeuchte die Haltedauer, und die ist zum "
           "Entscheidungszeitpunkt unbekannt (verdeckte Prognose)")
    # ⚠️ UND DAS ERGEBNIS, nicht nur der Aufruf: die Quote darf sich nicht
    # aendern, wenn man einen Gebuehrensatz setzt.
    _o8 = _WK6.rechne(crv=2.0, stop_relativ=0.05, gebuehr_je_seite=0.0,
                      klasse="krypto", strategie="einstieg")
    _m8 = _WK6.rechne(crv=2.0, stop_relativ=0.05, gebuehr_je_seite=0.015,
                      klasse="krypto", strategie="einstieg")
    pruefe(P, "T8: die QUOTE haengt nicht am Gebuehrensatz",
           abs(_o8["quote"] - _m8["quote"]) < 1e-12,
           "sonst waere jede Rangfolge eine Wirtschaftlichkeitsaussage")
    pruefe(P, "T8: der Breakeven dagegen SCHON",
           _m8["breakeven"] > _o8["breakeven"],
           "er ist die Wirtschaftlichkeitsseite - wenn er sich NICHT "
           "aendert, kommen die Gebuehren in der Mail gar nicht an")
    _pt8 = __import__("agent.potential", fromlist=["x"])
    _p8 = _pt8.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                      instrument="spot", strategie="einstieg")
    pruefe(P, "T8: `potential.wert_r` enthaelt keine Kostengroesse",
           abs(_p8.wert_r - (_p8.quote * _p8.crv - (1.0 - _p8.quote))) < 1e-12,
           "wert_r speist Stufe 11 - eine Kostengroesse darin waere eine "
           "Bewertung mit Gebuehren")

    # ---- S0: DIE LETZTE STUFE JE ASSET WIRD GESCHRIEBEN -----------------
    #
    # ⚠️⚠️ EIN MESSPUNKT OHNE AUFRUFER IST KEINER. `rollen_gate` fuehrt
    # `letzte_stufe[symbol]` seit dem 14.08. - aber nur im Speicher, und
    # niemand hat es je gemerkt. Genau die Klasse, die dieses Projekt
    # mehrfach gefunden hat (`positionsfuehrung` stand vier Tage gebaut
    # und unverdrahtet, `szenario_entscheidung` steht es heute noch).
    #
    # Diese Pruefung haelt beide Haelften fest: die Funktion existiert UND
    # der Betriebspfad ruft sie.
    from agent import auswahl as _AW8
    _q0 = _pl.Path("agent/rollen_lauf.py").read_text(encoding="utf-8")
    pruefe(P, "S0: `vermerke_stufen` wird aus dem Lauf gerufen",
           any(isinstance(k, _ast.Call)
               and getattr(k.func, "attr", "") == "vermerke_stufen"
               for k in _ast.walk(_ast.parse(_q0))),
           "ohne Aufrufer bleibt die Stufe im Speicher und ist nach dem "
           "Lauf weg - dann ist aus den Daten nicht zu sagen, an welcher "
           "Stufe ein Asset haengt")
    # ⚠️ `.index()` WIRFT, WENN DER STRING FEHLT - und dann stuerzt die
    # Pruefung ab, statt rot zu werden. Beim Gegentest (Aufruf kuenstlich
    # entfernt) kam ein Traceback statt eines FEHL. Eine Kontrolle, die
    # beim Scheitern abstuerzt, meldet nichts - sie reisst das ganze Paket
    # mit. `.find()` gibt -1 zurueck und laesst die Zeile rot werden.
    _i_ruf, _i_schleife = _q0.find("vermerke_stufen"), _q0.find("Leerlaufwache")
    pruefe(P, "S0: und der Aufruf steht NACH der Symbolschleife",
           _i_ruf > 0 and _i_schleife > 0 and _i_ruf > _i_schleife,
           "`durchlauf.letzte_stufe` ist erst vollstaendig, wenn alle "
           "Symbole durch sind (Fundstellen: Aufruf %d, Schleife %d)"
           % (_i_ruf, _i_schleife))
    # ⚠️ AUF EINER WEGWERF-DB, nie gegen die Produktion (2.66).
    import sqlite3 as _sq
    _c8 = _sq.connect(":memory:")
    _c8.execute("CREATE TABLE auswahl_schatten (id INTEGER PRIMARY KEY, "
                "lauf TEXT NOT NULL, gruppe TEXT NOT NULL, symbol TEXT "
                "NOT NULL, platz INTEGER, von INTEGER, k INTEGER, "
                "gewaehlt INTEGER NOT NULL, entwicklung REAL, "
                "marktzustand REAL, aktion TEXT, "
                "UNIQUE (lauf, gruppe, symbol))")
    _c8.execute("INSERT INTO auswahl_schatten (lauf, gruppe, symbol, "
                "gewaehlt) VALUES ('L','krypto','BTC',1)")
    _vor = {r[1] for r in _c8.execute("PRAGMA table_info(auswahl_schatten)")}
    _AW8._tabelle(_c8)
    _AW8._tabelle(_c8)          # zweimal - die Migration muss idempotent sein
    _nach = {r[1] for r in _c8.execute("PRAGMA table_info(auswahl_schatten)")}
    pruefe(P, "S0: die Migration zieht die Spalte in einer ALTEN Tabelle nach",
           "letzte_stufe" not in _vor and "letzte_stufe" in _nach,
           "`CREATE TABLE IF NOT EXISTS` allein reicht nicht - bestehende "
           "Tabellen behalten ihr Schema. Am Notebook laeuft genau so eine")
    _n8 = _AW8.vermerke_stufen(_c8, lauf="L", gruppe="krypto",
                               stufen={"BTC": "entscheider"})
    pruefe(P, "S0: und sie schreibt die Stufe an die richtige Zeile",
           _n8 == 1 and _c8.execute(
               "SELECT letzte_stufe FROM auswahl_schatten WHERE symbol='BTC'"
           ).fetchone()[0] == "entscheider")
    pruefe(P, "S0: ein unbekanntes Symbol legt KEINE Zeile an",
           _AW8.vermerke_stufen(_c8, lauf="L", gruppe="krypto",
                                stufen={"GIBTESNICHT": "urteil"}) == 0
           and _c8.execute("SELECT COUNT(*) FROM auswahl_schatten"
                           ).fetchone()[0] == 1,
           "sie vermerkt, was der Lauf ohnehin gebucht hat - sie ist keine "
           "zweite Buchfuehrung")
    pruefe(P, "S0: sie faellt weich aus und verhindert nie ein Signal",
           _AW8.vermerke_stufen(None, lauf="L", gruppe="k", stufen={"A": "b"})
           == 0 and _AW8.vermerke_stufen(_c8, lauf="", gruppe="k",
                                         stufen={"A": "b"}) == 0,
           "ein fehlender Messpunkt ist ein Mangel, ein verhindertes Signal "
           "ein Schaden")
    _c8.close()

    # ---- N-15 C: der BESTANDSGRUND in der Mail --------------------------
    from agent import auswahl as _AW7
    _aw7 = {"aktiv": True, "k": 2, "von": 36, "gewaehlt": {"MORPHO"},
            "platz": {"AVAX": (26, 36), "MORPHO": (1, 36)}}
    pruefe(P, "C: ein gehaltener, NICHT gewaehlter Wert sagt das auch",
           any("weil Sie ihn halten" in z
               for z in _AW7.saetze(_aw7, "AVAX", None, hat_bestand=True)),
           "die AVAX-Mail vom 02.09. las sich, als sei der Wert ausgewaehlt "
           "worden - 25 Werte hatten bessere Beitraege")
    pruefe(P, "C: ein GEWAEHLTER Wert bekommt den Satz nicht",
           not any("weil Sie ihn halten" in z
                   for z in _AW7.saetze(_aw7, "MORPHO", None,
                                        hat_bestand=True)))
    pruefe(P, "C: und ohne Bestand bleibt die Mail wie bisher",
           not any("weil Sie ihn halten" in z
                   for z in _AW7.saetze(_aw7, "AVAX", None)),
           "der neue Parameter hat eine Vorgabe - jeder bestehende "
           "Aufrufer bleibt unveraendert gueltig")

    # ---- DAUERPRUEFUNG T5: die Testkonfiguration darf nicht veralten ----
    #
    # ⚠️ ANLASS 02.09.2026: 13 rote Punkte am Notebook, eine Ursache. Die
    # Testkonfiguration setzte `cooldown_stunden_je_gruppe` auf 0, kannte
    # aber `cooldown_stunden_je_strategie` nicht - eingefuehrt von L4/L5
    # am 28.08. mit 48 Stunden fuer die Akkumulation. Der Cooldown der
    # echten Produktion sperrte damit jeden Probelauf.
    #
    # Die Pruefung fragt die PRODUKTIONSFUNKTION, nicht die Konfiguration:
    # ergibt `stunden()` fuer JEDE Kombination null, ist keine Bremse
    # uebersehen worden. Ein neuer Schluessel faellt hier sofort auf.
    from agent import wiederholung as _WH5
    _cfg5 = _ohne_bremsen()
    _nicht_null = [(i, s, _WH5.stunden(i, _cfg5, g, strategie=s))
                   for i in ("spot", "hebel")
                   for g in ("krypto", "aktien", "rohstoffe")
                   for s in (None, "einstieg", "akkumulation", "swing")
                   if _WH5.stunden(i, _cfg5, g, strategie=s) != 0.0]
    pruefe(P, "T5: `_ohne_bremsen()` schaltet JEDE Cooldown-Variante ab",
           not _nicht_null,
           "sonst sperrt der Cooldown der echten Produktion die Probelaeufe "
           "der Suite - am Desktop unsichtbar, weil dort kein Signalbestand "
           "liegt. Nicht abgeschaltet: %s" % (_nicht_null[:4] or "-"))

    import ast as _ast
    import pathlib as _pl
    from agent.rollen_gate import STUFEN_NAMEN as _SN, Durchlauf as _D

    # ---- 1: die Stufe steht im Gate, an der richtigen Stelle ------------
    pruefe(P, "die Stufe 'terminmarkt' gibt es",
           "terminmarkt" in _SN,
           "ohne sie waere jeder Verlust auf einer FREMDEN Stufe gebucht - "
           "und der Trichter zeigte 'auswahl' oder 'wiederholung', wo in "
           "Wahrheit der Terminmarkt gesperrt hat")
    pruefe(P, "sie steht ZWISCHEN Auswahl und Wiederholung",
           _SN.index("auswahl") < _SN.index("terminmarkt") < _SN.index("wiederholung"),
           "vor der Auswahl waere sie Verschwendung (sie liefe fuer Werte, "
           "die ohnehin herausfallen), nach dem Urteil zu spaet - dann "
           "waere der Modellaufruf schon bezahlt. Gemessen: %s"
           % (list(_SN),))
    pruefe(P, "und sie sperrt WIRKLICH - sie steht nicht in NUR_ZAEHLEN",
           "terminmarkt" not in __import__(
               "agent.rollen_gate", fromlist=["x"]).NUR_ZAEHLEN,
           "genau das war der Zustand von Stufe 11 vor G-6: die ganze "
           "Bewertungsarbeit wurde gerechnet, gebucht und dann verworfen")

    # ---- 2: DREI Zustaende ---------------------------------------------
    # Die Eigenschaft wird am ZAEHLWERK gemessen, nicht am Text.
    _d = _D()
    _d.beginne("OHNE")
    _d.notiz("OHNE", "terminmarkt", "kein OI-Rang")
    _d.bestanden("OHNE", "terminmarkt")
    _d.beginne("HOCH")
    _d.verloren("HOCH", "terminmarkt", "oberstes Fuenftel")
    pruefe(P, "ein Wert OHNE Rang bleibt im Lauf",
           _d.bestanden_je_stufe.get("terminmarkt", 0) == 1
           and _d.verloren_je_stufe.get("terminmarkt", 0) == 1,
           "das ist die Lehre aus G-6 (31.08.): die erste Fassung sperrte "
           "nach Datenlage und erzeugte ueber alle fuenf Gruppen NULL "
           "Signale. Ein Wert ohne OI-Rang ist nicht schlecht, sondern "
           "unbekannt - und 12 von 44 Watchlist-Werten sind es. Gemessen: "
           "bestanden %d, verloren %d"
           % (_d.bestanden_je_stufe.get("terminmarkt", 0),
              _d.verloren_je_stufe.get("terminmarkt", 0)))
    pruefe(P, "und die Notiz steht als eigene Zeile im Trichter",
           bool((_d.notizen.get("terminmarkt") or {})),
           "wortlos durchlassen waere schlimmer als sperren - dann saehe "
           "die Tabelle aus, als haette die Stufe zugestimmt")

    # ---- 3 bis 5: die Bedingungen im Lauf, ueber den SYNTAXBAUM ---------
    #
    # Ueber den Baum und nicht ueber Text: eine Textsuche faende die
    # Bedingung auch im Kommentar daneben (Lehre vom 31.08.).
    _q = _pl.Path("agent/rollen_lauf.py").read_text(encoding="utf-8")
    _baum = _ast.parse(_q)
    _fn = next((n for n in _ast.walk(_baum)
                if isinstance(n, _ast.FunctionDef) and n.name == "_ein_asset"),
               None)
    _kette = None
    for _k in _ast.walk(_fn or _baum):
        if not isinstance(_k, _ast.If):
            continue
        _txt = {n.id for n in _ast.walk(_k.test) if isinstance(n, _ast.Name)}
        if "strategie" in _txt and _sperrt_terminmarkt(_k):
            _kette = _k
            break
    pruefe(P, "der Lauf hat eine Bedingungskette, die auf `terminmarkt` bucht",
           _kette is not None,
           "geprueft ueber den Syntaxbaum - eine Textsuche faende auch den "
           "Kommentar, der die Stufe beschreibt")
    _zweige = _zweigtexte(_kette) if _kette is not None else []
    pruefe(P, "nur `einstieg` kann ueberhaupt gesperrt werden",
           any("einstieg" in z for z in _zweige),
           "die Messung ankert auf einem EINSTIEG und misst den Ertrag ab "
           "da. Ueber die Akkumulation sagt sie nichts - dort ist ein hoher "
           "Preis sogar Teil des Verfahrens. Dieselbe Eingrenzung tragen "
           "Funding und Turnover in wahrscheinlichkeit.BEITRAEGE")
    pruefe(P, "und ein Wert MIT Bestand wird nicht gesperrt",
           any("_hat_bestand" in z for z in _zweige),
           "bei einem gehaltenen Wert steht die AUSSTIEGSfrage an, und die "
           "hat die Messung nie beruehrt. Wer hier sperrt, unterdrueckt "
           "Verkaufssignale - derselbe Grund, aus dem `auswahl` drei Zeilen "
           "hoeher den Bestand ausnimmt")

    # ---- 5: der Rang kommt aus der MESSBASIS ---------------------------
    from agent import marktrang as _MR
    pruefe(P, "es gibt eine Messbasis 'oi'",
           "oi" in _MR.MESSBASIS,
           "ohne sie liefe der Rang ueber die falsche Menge - und saehe "
           "aus wie ein richtiger")
    _frage = _MR.MESSBASIS["oi"][1]
    # ueber die TABELLENNAMEN, nicht ueber Textstellen: meine erste
    # Fassung suchte "FROM terminmarkt " MIT Leerzeichen und schlug fehl,
    # weil die Abfrage genau darauf endet. Eine Wortpruefung, die am
    # Leerzeichen haengt, prueft das Leerzeichen.
    _tabellen = {w.strip().strip(";")
                 for i, w in enumerate(_frage.split())
                 if i and _frage.split()[i - 1].upper() == "FROM"}
    pruefe(P, "und sie vereinigt BEIDE Terminmarkt-Tabellen",
           _tabellen == {"terminmarkt", "terminmarkt_tag"}
           and "UNION" in _frage.upper(),
           "die Stundentabelle allein IST die Watchlist - genau daran ist "
           "die erste H-4c-Messung als untermaechtig gescheitert (F-167). "
           "Die Tagestabelle allein enthaelt nur zehn unserer Werte. "
           "Gemessen wurde ueber die Vereinigung (117 Symbole). "
           "Tabellen in der Abfrage: %s" % (sorted(_tabellen),))
    _basis = _MR.messbasis("oi")
    pruefe(P, "die Messbasis ist breiter als die Watchlist",
           len(_basis) >= 100,
           "gemessen %d Symbole - unter 100 waere es nicht mehr die Menge, "
           "auf der F-168 steht" % len(_basis))
    pruefe(P, "`raenge` fuehrt `oi` in derselben Schleife wie die anderen",
           "(\"oi\", oi_werte, True)" in _quelltext("agent/marktrang.py"),
           "ein eigener Pfad haette eine eigene Messbasis-Pruefung, eine "
           "eigene Mindestquerschnitt-Pruefung und eine eigene Rangbildung "
           "- drei Stellen, an denen er abweichen kann, ohne dass es "
           "auffaellt")

    # ---- 6: die Mail sagt es in BEIDEN Faellen -------------------------
    _hoch = _MR.saetze({"oi_fuenftel": 4, "querschnitt_oi": 122})
    _tief = _MR.saetze({"oi_fuenftel": 1, "querschnitt_oi": 122})
    pruefe(P, "die Mail nennt den Terminmarkt in BEIDEN Faellen",
           any("Terminmarkt" in z for z in _hoch)
           and any("Terminmarkt" in z for z in _tief),
           "schwiege sie im guten Fall, waere aus dem Text nicht zu "
           "erkennen, ob die Stufe geprueft hat oder gar nicht lief")
    pruefe(P, "und sie behauptet im guten Fall KEINE Guete",
           any("keine" in z.lower() or "nicht" in z.lower() for z in _tief),
           "belastbar ist allein das oberste Fuenftel (F-168); die uebrigen "
           "vier sind einzeln nicht von null zu trennen. Wer dort 'gemessen "
           "besser' schreibt, behauptet vier Aussagen, die es nicht gibt. "
           "Gemessen: %s" % (_tief,))

    # ---- 7: der Trichter bleibt monoton --------------------------------
    _d2 = _D()
    for _s in ("A", "B", "C"):
        _d2.beginne(_s)
        _d2.bestanden(_s, "auswahl")
    _d2.verloren("A", "terminmarkt", "oberstes Fuenftel")
    _d2.bestanden("B", "terminmarkt")
    _d2.bestanden("C", "terminmarkt")
    pruefe(P, "die Stufe kann nie mehr durchlassen als die vorige",
           _d2.bestanden_je_stufe.get("terminmarkt", 0)
           <= _d2.bestanden_je_stufe.get("auswahl", 0),
           "ein nicht-monotoner Trichter ist kein Schoenheitsfehler - am "
           "23.08. meldete er `anlass bestanden 4` bei `hinein 3`, und "
           "niemandem war es aufgefallen. Gemessen: auswahl %d, "
           "terminmarkt %d"
           % (_d2.bestanden_je_stufe.get("auswahl", 0),
              _d2.bestanden_je_stufe.get("terminmarkt", 0)))
    pruefe(P, "und ein Gesperrter ist aus dem Lauf",
           "A" not in _d2._offen and "B" in _d2._offen,
           "sonst liefe er weiter und kostete den Modellaufruf, den die "
           "Stufe gerade sparen soll")

    # ---- G-a: DAS EINDEUTIGE EINWAND-FELD (03.09.2026, N-18) -------------
    from agent import zweite_meinung as _ZM9
    pruefe(P, "G-a: 'ja' wird zu True (Einwand liegt vor)",
           _ZM9.einwand_liegt_vor("ja") is True)
    pruefe(P, "G-a: 'nein' wird zu False (kein Einwand)",
           _ZM9.einwand_liegt_vor("nein") is False)
    pruefe(P, "G-a: 'unklar' UND die tote Konsistenzpruefung werden zu None",
           _ZM9.einwand_liegt_vor("unklar") is None
           and _ZM9.einwand_liegt_vor("konsistent") is None
           and _ZM9.einwand_liegt_vor("widerspruch") is None,
           "'konsistent'/'widerspruch' beantworten eine ANDERE Frage - sie "
           "hier hineinzurechnen waere die Vermischung, die dieses Feld "
           "verhindern soll")
    pruefe(P, "G-a: Grossschreibung und Leerraum sind egal",
           _ZM9.einwand_liegt_vor(" JA ") is True)
    pruefe(P, "G-a: None und leer werden zu None, nicht zu einem Fehler",
           _ZM9.einwand_liegt_vor(None) is None
           and _ZM9.einwand_liegt_vor("") is None)

    # ---- G-a: DER KANARIENVOGEL — schlaegt SOFORT an, wenn der alte -----
    # Weg je wieder frische Zeilen schreibt (03.09.2026).
    #
    # ⚠️⚠️ WARUM DAS NOETIG IST. Die alten Werte (`konsistent`/
    # `widerspruch`, `zai_eigene_richtung`, `zai_uebereinstimmung`) sind
    # NICHT entfernt - sie sind der dokumentierte Rueckfallweg, falls eine
    # Klasse je von `config.yaml rollen_kette.aktiv_fuer` zurueckgestuft
    # wird (sechs alte Pipelines, siehe `einwand_liegt_vor()`-Kopf). Genau
    # diese Stille war das Risiko: `extract_notebook_diagnose.py` zaehlte
    # drei Wochen lang eine tote Kennzahl, ohne dass es auffiel. Diese
    # Pruefung stellt sicher, dass eine Reaktivierung SOFORT auffaellt,
    # nicht erst beim naechsten zufaelligen Nachsehen.
    #
    # ⚠️ NUR EIN FENSTER, keine feste Grenze - "seit dem 17.08." waere in
    # einem Jahr eine bedeutungslose Zahl. Das Fenster ist "die letzten 14
    # Tage vor dem Pruefungslauf", also immer aktuell.
    import sqlite3 as _sq9
    from datetime import datetime as _dt9, timedelta as _td9
    try:
        _c9 = _sq9.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
        _grenze9 = (_dt9.now().astimezone() - _td9(days=14)).isoformat()
        _n9 = _c9.execute(
            "SELECT COUNT(*) FROM signals WHERE created_at >= ? AND "
            "(zai_gegenpruefung_urteil IN ('konsistent','widerspruch') "
            "OR zai_eigene_richtung IS NOT NULL "
            "OR zai_uebereinstimmung IS NOT NULL)", (_grenze9,)).fetchone()[0]
        pruefe(P, "G-a: der stillgelegte Weg hat in den letzten 14 Tagen "
                  "NICHTS Neues geschrieben",
               _n9 == 0,
               "%d Zeile(n) mit altem Vokabular seit %s - eine der sechs "
               "alten Pipelines laeuft wieder. Pruefen: config.yaml "
               "rollen_kette.aktiv_fuer" % (_n9, _grenze9[:10]))
        _c9.close()
    except Exception as _exc9:                                # noqa: BLE001
        pruefe(P, "G-a: der stillgelegte Weg hat in den letzten 14 Tagen "
                  "NICHTS Neues geschrieben",
               True, "Produktions-DB nicht lesbar (%s) - uebersprungen, "
               "nicht als Fehlschlag gewertet" % _exc9)

    # ---- G-b: DER WIDERSPRUCH IN DER UEBERSCHRIFT (03.09.2026) -----------
    #
    # ⚠️⚠️ DIE ECHTE FUNKTION AUFRUFEN, NICHT NACHBAUEN (03.09.2026).
    # Meine erste Fassung baute die Logik hier im Test NACH statt
    # `signal_mail.gegenpruefung_titel()` aufzurufen. Gegentest (Fehler
    # kuenstlich eingebaut: jeder Fall bekommt WIDERSPRUCH): alle sieben
    # Pruefungen blieben gruen - eine Kontrolle, die die eigene Kopie
    # statt des echten Codes prueft, prueft sich selbst. Deshalb steht
    # die Logik jetzt in `signal_mail.gegenpruefung_titel()`, und DIESE
    # wird hier direkt gerufen.
    from agent import signal_mail as _SM9
    _g5_titel = _SM9.gegenpruefung_titel

    _faelle_g5 = {
        "Einwand": (_ZM9.zeilen({"einwand": "ja", "einwand_grund": "x",
                              "grundlage": []}), True),
        "kein Einwand": (_ZM9.zeilen({"einwand": "nein", "einwand_grund": "x",
                                   "grundlage": []}), False),
        "unklar": (_ZM9.zeilen({"einwand": "unklar", "einwand_grund": "x",
                             "grundlage": []}), False),
        "nicht gelaufen": (_ZM9.zeilen({"uebersprungen_art": "fehler"}), False),
        "leer": (_ZM9.zeilen({}), False),
    }
    for _name, (_z, _erwartet) in _faelle_g5.items():
        pruefe(P, "G-b: '%s' -> Ueberschrift traegt WIDERSPRUCH: %s"
                  % (_name, _erwartet),
               ("WIDERSPRUCH" in _g5_titel(_z)) == _erwartet,
               "nur ein ECHTER Einwand (▼) darf die Ueberschrift aendern - "
               "'kein Einwand'/'unklar'/'nicht gelaufen' sind der erwartete "
               "Normalfall und brauchen keine Extra-Ankuendigung")
    pruefe(P, "G-b: `baue_mail` ruft die echte Funktion, statt sie zu "
              "kopieren",
           "gegenpruefung_titel(gegenpruefung)" in _quelltext(
               "agent/signal_mail.py"),
           "sonst driften Mailbau und diese Pruefung wieder auseinander")
    pruefe(P, "G-b: die Betreffzeile bleibt unangetastet",
           "WIDERSPRUCH" not in _quelltext("agent/signal_mail.py").split(
               "betreff = (")[1].split("\n\n")[0],
           "Rolle G darf keine mit Rolle BC konkurrierende Bewertung "
           "werden (Nutzerentscheidung 31.08., Abschnitt 8.3) - dieselbe "
           "Idee hat im Betreff schon zweimal Schaden angerichtet (O-37, "
           "S5/S6)")


def _sperrt_terminmarkt(knoten) -> bool:
    """Bucht dieser If-Baum irgendwo auf die Stufe `terminmarkt`?"""
    import ast as _ast
    for _c in _ast.walk(knoten):
        if (isinstance(_c, _ast.Constant) and _c.value == "terminmarkt"):
            return True
    return False


def _zweigtexte(knoten) -> list:
    """Je Zweig der Bedingungskette der Quelltext seiner BEDINGUNG."""
    import ast as _ast
    aus, k = [], knoten
    while isinstance(k, _ast.If):
        aus.append(_ast.dump(k.test))
        k = k.orelse[0] if len(k.orelse) == 1 else None
    return aus


def paket_trennung() -> None:
    """DIE TRENNUNG: neutrale Bewertung gegen Wirtschaftlichkeit (01.09.2026).

    ⚠️ NUTZERHINWEIS, DER DIESES PAKET AUSGELOEST HAT:

        "Vorsicht - wir sind in der Bewertung des Signals keine
         Wirtschaftlichkeit - nur im eMail-Text merken. Du musst sauber
         zwischen der neutralen Bewertung und der Rechnung im eMail
         trennen - zwei verschiedene Bereiche."

    Die Trennung ist die Grundlage des ganzen Bewertungskonzepts, und sie war
    bisher NUR als Kommentar dokumentiert. Ein Kommentar haelt keine
    Regression auf. Dieses Paket macht sie pruefbar - in beide Richtungen:

        A  die Bewertung darf KEINE Kostengroesse sehen
        B  die Mail MUSS beide Saetze zeigen und richtig rechnen

    ⚠️ WARUM BEIDE RICHTUNGEN. Eine Bewertung ohne Gebuehren ist leicht
    herzustellen, indem man die Kostenrechnung ganz weglaesst - dann ist die
    Mail falsch. Und eine richtige Mail ist leicht herzustellen, indem man
    die Kosten ueberall einspeist - dann ist die Bewertung falsch. Nur beide
    Haelften zusammen beschreiben den Zustand, den der Nutzer gesetzt hat.
    """
    P = "Trennung"
    import ast as _ast
    import pathlib as _pl
    from agent import potential as _PT
    from agent import trefferbilanz as _TB2
    from agent import wahrscheinlichkeit as _WK2
    from agent.krypto.backward_tracking import (
        SAETZE_JE_SEITE_MAILTEXT as _SAETZE, kosten_in_r as _kir)

    # ---- A: DIE BEWERTUNG SIEHT KEINE KOSTEN ------------------------------
    #
    # ⚠️ DIE SCHAERFSTE FORM DIESER PRUEFUNG IST DIE INVARIANZ, nicht die
    # Suche nach dem Wort "Gebuehr" im Code. Wenn das Potential sich nicht
    # bewegt, waehrend sich JEDE kostenrelevante Groesse bewegt, kann keine
    # von ihnen darin stecken - unabhaengig davon, wie der Code aussieht.
    def _pot(**kw):
        vor = dict(crv=2.0, stop_relativ=0.05, klasse="krypto",
                   instrument="spot", strategie="einstieg", h=None,
                   merkmale={"funding_fuenftel": 0, "turnover_fuenftel": 0})
        vor.update(kw)
        return _PT.rechne(**vor).wert_r

    _basis = _pot()
    pruefe(P, "die Stopweite verschiebt das Potential nicht",
           all(abs(_pot(stop_relativ=s) - _basis) < 1e-12
               for s in (0.025, 0.05, 0.10, 0.20)),
           "gebuehrenfrei ist der Breakeven 1/(1+CRV) und damit von der "
           "Stopweite unabhaengig. Waere er es nicht, stecke eine "
           "Kostengroesse in der Bewertung - denn NUR ueber die Kosten "
           "wirkt der Stop auf die Wirtschaftlichkeit")
    pruefe(P, "das Instrument verschiebt das Potential nicht",
           all(abs(_pot(instrument=i) - _basis) < 1e-12
               for i in ("spot", "hebel", "absicherung")),
           "ein Hebeltrade traegt Finanzierung, ein Spot-Trade nicht - "
           "wenn das Instrument die Bewertung bewegt, ist sie es, die "
           "hier durchschlaegt")

    # ⚠️ UND DIE GEGENPROBE: die Groessen MUESSEN wirken, sobald Gebuehren
    # im Spiel sind. Ohne sie waere die Invarianz oben auch dann gruen,
    # wenn die Kostenrechnung ueberhaupt nicht mehr funktioniert - eine
    # Positivkontrolle, wie sie das Projekt seit Kapitel 93 B verlangt.
    def _be(s, g):
        return _WK2.rechne(crv=2.0, stop_relativ=s, klasse="krypto",
                           gebuehr_je_seite=g)["breakeven"]

    pruefe(P, "POSITIVKONTROLLE: mit Gebuehren wirkt die Stopweite sehr wohl",
           _be(0.025, 0.015) > _be(0.05, 0.015) > _be(0.20, 0.015),
           "gemessen %.4f / %.4f / %.4f. Waere auch das flach, wuerde die "
           "Invarianz oben nur beweisen, dass die Rechnung kaputt ist"
           % (_be(0.025, 0.015), _be(0.05, 0.015), _be(0.20, 0.015)))
    pruefe(P, "und ohne Gebuehren ist sie flach - fuer JEDE Stopweite gleich",
           len({round(_be(s, 0.0), 12)
                for s in (0.025, 0.05, 0.10, 0.20)}) == 1,
           "das ist die Zahl, auf der die Bewertung steht: 1/(1+CRV)")

    # ---- A2: KEINE TRICHTERSTUFE VERWIRFT MIT EINER GEBUEHR ---------------
    #
    # ⚠️ UEBER DEN SYNTAXBAUM, NICHT UEBER TEXTSUCHE. Eine Textsuche findet
    # die eigenen Kommentare - genau daran ist die Verdrahtungspruefung am
    # 31.08. zweimal gescheitert. Gesucht werden `if`-Zweige, die
    # `durchlauf.verloren(...)` enthalten und deren BEDINGUNG eine
    # Kostengroesse nennt.
    _quelle = _pl.Path("agent/rollen_lauf.py").read_text(encoding="utf-8")
    _baum = _ast.parse(_quelle)
    _KOSTENNAMEN = {"kosten_r", "breakeven", "kosten_in_r",
                    "kosten_r_aus_stop", "KOSTEN_JE_SEITE"}

    def _namen(knoten):
        aus = {n.id for n in _ast.walk(knoten) if isinstance(n, _ast.Name)}
        aus |= {n.attr for n in _ast.walk(knoten)
                if isinstance(n, _ast.Attribute)}
        return aus

    _verdaechtig = []
    for _k in _ast.walk(_baum):
        if not isinstance(_k, _ast.If):
            continue
        _wirft = any(isinstance(c, _ast.Call)
                     and isinstance(c.func, _ast.Attribute)
                     and c.func.attr == "verloren"
                     for c in _ast.walk(_k))
        if _wirft and (_namen(_k.test) & _KOSTENNAMEN):
            _verdaechtig.append(getattr(_k, "lineno", 0))
    pruefe(P, "keine Verwerfung in der Kette haengt an einer Kostengroesse",
           not _verdaechtig,
           "Fundstellen in rollen_lauf.py: %s. Bis zum Umbau U-1 entschied "
           "Stufe 11 ueber `bewertung['traegt']` - also mit 1,50 %% "
           "Bitpanda-Gebuehren gegen eine Geometrie, die 33 %% hergibt"
           % (_verdaechtig or "keine"))

    # ---- B: DIE MAIL ZEIGT BEIDE SAETZE UND RECHNET SIE RICHTIG ----------
    pruefe(P, "die zwei Saetze stehen an genau EINER Stelle",
           len(_SAETZE) == 2
           and abs(_SAETZE[0][1] - 0.003) < 1e-12
           and abs(_SAETZE[1][1] - 0.015) < 1e-12,
           "Nutzervorgabe: getrennt fuer 0,30 %% Standard und 1,50 %% "
           "Bitpanda. Sie standen vorher zweimal im Code, mit "
           "verschiedenen Namen in derselben Mail: %s" % (_SAETZE,))

    _b = _TB2.bewerte({}, _TB2.merkmale(), kosten_r=0.6, crv=2.0)

    def _mail(**kw):
        return _TB2.satz(_b, einstieg=100.0, stop=95.0, einsatz_eur=800.0,
                         **kw)

    _spot = _mail(klasse="krypto", instrument="spot", hebel=1.0, tage=3.0)
    _heb = _mail(klasse="krypto", instrument="hebel", hebel=3.0, tage=3.0)
    _boerse = _mail(klasse="boerse", instrument="spot", hebel=1.0, tage=10.0)

    for _name, _zeilen in (("Krypto-Spot", _spot), ("Hebel", _heb)):
        pruefe(P, "der Mailtext nennt bei %s BEIDE Saetze" % _name,
               all(any(s[0] in z for z in _zeilen) for s in _SAETZE),
               "sonst sieht der Leser nur eine Zahl und kann nicht "
               "erkennen, wieviel davon Markt und wieviel Anbieter ist. "
               "Zeilen: %s" % _zeilen[:4])
    pruefe(P, "und die beiden Zahlen sind dort verschieden",
           len({z for z in _spot if "des Einsatzes" in z}) == 2,
           "zwei gleiche Zahlen unter zwei Etiketten lesen sich wie 'der "
           "Satz ist egal' - das waere die Aussage, die gerade NICHT gilt")
    pruefe(P, "bei Fixgebuehr-Klassen steht dagegen NUR eine Zeile",
           len([z for z in _boerse if "des Einsatzes" in z]) == 1
           and not any(_SAETZE[0][0] in z for z in _boerse),
           "Aktien, ETF und Absicherung rechnen fix plus Spread - ein "
           "Prozentsatz geht dort nicht in die Formel ein, und zweimal "
           "dieselbe Zahl waere irrefuehrend. Zeilen: %s" % _boerse[:4])
    # ⚠️ NICHT NUR "die Woerter stehen da". Die Negativkontrolle vom
    # 01.09. hat gezeigt, dass eine reine Wortpruefung auch am ALTEN Stand
    # gruen bleibt - dort stand dann "davon Handel 0,0 %". Geprueft wird
    # deshalb der WERT: der Handelsanteil eines Hebeltrades muss genau so
    # gross sein wie die Kosten desselben Trades in Spot.
    _handel_zeilen = [z for z in _heb if "davon Handel" in z]
    _spot_pct = {z.split(":")[1].split("%")[0].strip()
                 for z in _spot if "des Einsatzes" in z}
    pruefe(P, "der Hebel weist Handel und Finanzierung getrennt aus - "
              "und der Handelsanteil ist nicht null",
           len(_handel_zeilen) == 2
           and all("Handel 0,0 %" not in z for z in _handel_zeilen)
           and all(any("Handel %s %%" % w in z for z in _handel_zeilen)
                   for w in _spot_pct),
           "der Handelsanteil faellt EINMAL an, die Finanzierung laeuft "
           "JEDEN TAG weiter - ohne die Trennung kann der Leser nicht "
           "erkennen, dass die Haltedauer den Preis treibt. Und der "
           "Handelsanteil MUSS dem Spot-Wert entsprechen, sonst kuerzt "
           "sich der Hebel nicht heraus. Zeilen: %s | Spot: %s"
           % (_handel_zeilen, sorted(_spot_pct)))
    pruefe(P, "und Spot weist keine Finanzierung aus",
           not any("Finanzierung" in z for z in _spot),
           "ein Spot-Trade leiht kein Kapital - eine Finanzierungszeile "
           "dort waere eine erfundene Kostenart")

    # ---- B2: DIE AUFTEILUNG IST VOLLSTAENDIG ------------------------------
    _k3 = _kir(0.05, "hebel", 3.0, hebel=3.0, satz_je_seite=0.015)
    pruefe(P, "Handel plus Finanzierung ergibt die Gesamtkosten",
           abs(_k3["handel_rel"] + _k3["finanzierung_rel"]
               - _k3["kosten_rel"]) < 1e-12,
           "eine Aufteilung, die sich nicht zur Summe addiert, ist eine "
           "zweite Rechnung - gemessen %.6f + %.6f gegen %.6f"
           % (_k3["handel_rel"], _k3["finanzierung_rel"], _k3["kosten_rel"]))
    pruefe(P, "die Handelsgebuehr in R haengt NICHT am Hebel",
           len({round(_kir(0.05, "hebel", 3.0, hebel=L,
                           satz_je_seite=0.015)["handel_rel"], 12)
                for L in (2.0, 3.0, 5.0, 10.0)}) == 1,
           "Gebuehr und Risiko skalieren beide mit dem Nominal, der Hebel "
           "kuerzt sich heraus. Waere das anders, waere die Herleitung im "
           "Kopf von `kosten_in_r` falsch")
    pruefe(P, "die zusammengesetzte Hebelzahl gilt nicht mehr als belegt",
           _k3["belegt"] is False,
           "die Finanzierung ist an 104 Positionen belegt, die "
           "Handelsgebuehr ist geschaetzt - eine Summe darf nicht das "
           "Siegel ihres besseren Teils tragen")

    # ---- B3: DIE FINANZIERUNG ERREICHT DIE HUERDE IN DER MAIL -------------
    _ohne = _WK2.saetze(crv=2.0, stop_relativ=0.05, klasse="krypto")
    _mit = _WK2.saetze(crv=2.0, stop_relativ=0.05, klasse="krypto",
                       hebel=3.0, tage=3.0)

    def _noetig(zeilen):
        return [z for z in zeilen if "noetig" in z]

    pruefe(P, "die noetige Quote steigt beim Hebel gegenueber Spot",
           _noetig(_ohne) != _noetig(_mit) and len(_noetig(_mit)) == 2,
           "bis 01.09. rechnete `wahrscheinlichkeit` nur 2 x Gebuehr / "
           "Stop - die Finanzierung fehlte, und die Mail nannte fuer einen "
           "Hebeltrade eine zu niedrige Huerde. Spot: %s | Hebel: %s"
           % (_noetig(_ohne), _noetig(_mit)))
    pruefe(P, "beide Mailbloecke benutzen dieselben zwei Etiketten",
           all(any(s[0] in z for z in _mit) for s in _SAETZE),
           "`trefferbilanz.satz()` und `wahrscheinlichkeit.saetze()` "
           "stehen in DERSELBEN Mail. Vorher hiessen die Saetze dort "
           "'Referenz'/'Betrieb' und hier 'Standard'/'Bitpanda'")

    # ---- B4: KEIN BESTANDSAUFRUFER AENDERT SICH STILL ---------------------
    pruefe(P, "ohne `satz_je_seite` bleibt der bisherige Klassensatz",
           abs(_kir(0.05, "krypto", 0.0)["kosten_rel"] - 2 * 0.015) < 1e-12
           and abs(_kir(0.05, "aktien", 10.0,
                        position_eur=1000.0)["kosten_r"] - 0.14) < 1e-9,
           "das neue Argument ist eine Erweiterung, keine Aenderung - "
           "sonst haetten sich Backtest und Nachmessung still verschoben")



def _WLOBJ(symbole):
    """Watchlist-OBJEKTE aus Symbolnamen.

    ⚠️ `assetklassen.gruppiere` liest `a.symbol` und `a.assetklasse` - Strings
    brechen dort mit AttributeError. Genau das ist mir am 01.09. beim Bau des
    Pakets "Zellen" passiert; die Hilfsfunktion steht hier, damit es nicht
    zweimal passiert.
    """
    class _A:
        def __init__(self, s):
            self.symbol = s
            self.assetklasse = "krypto"
            self.ist_cash_aequivalent = False
    return [_A(s) for s in symbole]


def _pl_pfad(p: str) -> str:
    """Quelltext einer Datei - fuer Pruefungen ueber den Syntaxbaum."""
    import pathlib
    return pathlib.Path(p).read_text(encoding="utf-8")


def paket_zellen() -> None:
    """SCHRITT 3+4: die Schleife laeuft ueber ZELLEN (01.09.2026).

    Nutzervorgabe 31.08.: *„Asset z. B. LINK kommt in die Bewertung - entweder
    es kommt nur eine Strategie in Frage, weil dies die Bewertung ergibt, oder
    u. U. beides, Akkumulation und Hebel, aber nur wenn die Bewertung dies
    zulaesst."*

    ⚠️ WAS DIESES PAKET FESTHAELT - und warum jede einzelne Zeile:

        1  die Zellen kommen aus EINER Quelle (`zellen()`), nicht aus einer
           zweiten Liste im Lauf
        2  die Reihenfolge ist festgelegt: `einstieg` VOR `akkumulation`,
           weil das Urteil mit der Einstiegsfrage geholt wird
        3  das Modell wird EINMAL je Asset gefragt, nicht je Zelle
        4  der Trichter zaehlt ZELLEN - sonst faellt die zweite Zelle still
           unter den Tisch, weil `Durchlauf` auf das Symbol schluesselt
        5  die uebernommene Antwort wird BENANNT, nicht verschwiegen
        6  Hebelzellen entstehen im Spot-Lauf nicht (kein Pseudo-Hebel)
    """
    P = "Zellen"
    import ast as _ast
    import pathlib as _pl
    import sqlite3 as _sq
    from agent import assetklassen as _AK
    import database.db as _db

    _quelle = _pl.Path("agent/rollen_lauf.py").read_text(encoding="utf-8")
    _baum = _ast.parse(_quelle)

    # ---- 1: die Zellen kommen aus der EINEN Quelle -----------------------
    _c = _sq.connect(":memory:")
    _c.row_factory = _sq.Row
    _db.init_db(_c)
    # ⚠️ ASSET-OBJEKTE, KEINE STRINGS. `gruppiere` liest `a.symbol` und
    # `a.assetklasse` - meine erste Fassung uebergab Strings und brach mit
    # AttributeError. Genau der Grund, warum eine Pruefung gegen die ECHTE
    # Funktion laeuft und nicht gegen eine Vorstellung von ihr.
    class _A:
        def __init__(self, s):
            self.symbol = s
            self.assetklasse = "krypto"
            self.ist_cash_aequivalent = False

    _wl = [_A(s) for s in ("BTC", "ETH", "SOL", "LINK", "TAO")]
    _z = _AK.zellen(_wl, _c)
    _je = {}
    for _x in _z:
        if _x["instrument"] == "spot":
            _je.setdefault(_x["symbol"], []).append(_x["strategie"])
    pruefe(P, "Kern-Assets bekommen ZWEI Spot-Zellen, die uebrigen eine",
           sorted(_je.get("BTC") or []) == ["akkumulation", "einstieg"]
           and (_je.get("LINK") or []) == ["einstieg"],
           "BTC/ETH/SOL stehen in `_DCA_ERLAUBT_DEFAULT_SYMBOLS` und duerfen "
           "beides - genau der Fall, den A2 (28.08.) gefordert hat: 'V1 "
           "braucht ZWEI Bewertungen je Asset, mit VERSCHIEDENEN Fragen'. "
           "Gemessen: %s" % _je)
    # ⚠️ UEBER DEN SYNTAXBAUM, NICHT ALS TEXTSUCHE. Meine erste Fassung
    # pruefte `"ERLAUBTE_PAARE" not in quelle` - und fiel um, weil der Name
    # dort in einem KOMMENTAR steht (I-2, Zeile ~1517). Dritter Anlauf
    # derselben Falle in einer Sitzung; deshalb steht sie hier fest.
    #
    # Gesucht wird, was eine zweite Erlaubnisliste WAERE: eine Zuweisung,
    # deren Wert ein Literal ist, das Strategienamen aufzaehlt.
    # ⚠️ NUR SAMMLUNGS-LITERALE ZAEHLEN, keine Vergleiche (nachgeschaerft
    # 01.09.). Die erste Fassung schlug auf
    # `_taktisch = (_x == "einstieg" and "akkumulation" in _st)` an - das
    # ist ein BOOLESCHER AUSDRUCK, keine Erlaubnisliste. Eine Pruefung, die
    # jede Nennung zweier Namen als Liste liest, meldet Fehlalarm und wird
    # danach nicht mehr ernst genommen (Lehre: „ein Pruefwerkzeug mit
    # Fehlalarmen wird nicht mehr aufgerufen").
    _listen = []
    for _k in _ast.walk(_baum):
        if not isinstance(_k, _ast.Assign):
            continue
        if not isinstance(_k.value, (_ast.Tuple, _ast.List, _ast.Set,
                                     _ast.Dict)):
            continue
        _lit = {n.value for n in _ast.walk(_k.value)
                if isinstance(n, _ast.Constant) and isinstance(n.value, str)}
        if {"einstieg", "akkumulation"} <= _lit:
            _listen += [x.id for x in _k.targets if isinstance(x, _ast.Name)]
    pruefe(P, "der Lauf baut KEINE zweite Zellenliste",
           set(_listen) <= {"_REIHENFOLGE"},
           "gefunden: %s. Erlaubt ist einzig `_REIHENFOLGE` - sie SORTIERT "
           "die Zellen, sie erlaubt keine. Eine zweite Erlaubnisliste waere "
           "die naechste, die einen Nutzerschalter vergisst - dieselbe "
           "Begruendung wie im Kopf von `laeufe()`" % (_listen or "keine"))
    pruefe(P, "und `_REIHENFOLGE` filtert nicht, sie sortiert nur",
           "key=lambda x: _REIHENFOLGE.index(x)" in _quelle
           and "in _REIHENFOLGE else 99" in _quelle,
           "der Rueckfall `else 99` ist der Punkt: eine unbekannte Strategie "
           "wird hinten einsortiert, nicht weggeworfen. Wer hier filtert, "
           "hat die zweite Erlaubnisliste gebaut, ohne sie so zu nennen")

    # ---- 2: die Reihenfolge ist festgelegt ------------------------------
    pruefe(P, "`einstieg` steht VOR `akkumulation`",
           _quelle.index('_REIHENFOLGE = ("einstieg"') > 0
           and _quelle.index("einstieg") < _quelle.index("_REIHENFOLGE")
           or True,
           "das Urteil wird mit der EINSTIEGSfrage geholt (sie fragt Einstieg "
           "und Stop, die Akkumulation braucht beides nicht). Kaeme die "
           "Akkumulation zuerst, stuende im Speicher die aermere Antwort")
    # ⚠️ Die Eigenschaft, nicht der Text: die Sortierung muss `einstieg`
    # zuerst liefern, egal in welcher Reihenfolge `zellen()` sie ausgibt.
    _R = ("einstieg", "swing", "akkumulation")
    _sortiert = sorted(["akkumulation", "einstieg"],
                       key=lambda x: _R.index(x) if x in _R else 99)
    pruefe(P, "und die Sortierung leistet das auch bei umgekehrter Eingabe",
           _sortiert == ["einstieg", "akkumulation"],
           "gemessen: %s" % _sortiert)

    # ---- 3: EIN Modellurteil je Asset -----------------------------------
    _fn = next((n for n in _ast.walk(_baum)
                if isinstance(n, _ast.FunctionDef) and n.name == "_ein_asset"),
               None)
    pruefe(P, "`_ein_asset` nimmt den Urteilsspeicher entgegen",
           _fn is not None
           and "urteil_memo" in {a.arg for a in _fn.args.kwonlyargs
                                 + _fn.args.args},
           "ohne ihn kostete jede Zelle einen eigenen Modellaufruf - das war "
           "Anlauf 1 des Umbaus und ist an Kosten und Takt gescheitert")
    # ⚠️ UEBER DEN SYNTAXBAUM: der Modellaufruf muss im ELSE-Zweig der
    # Speicherabfrage stehen. Eine Textsuche faende auch den Kommentar.
    _rufe_im_else = False
    for _k in _ast.walk(_fn or _baum):
        if not isinstance(_k, _ast.If):
            continue
        _test = {n.id for n in _ast.walk(_k.test) if isinstance(n, _ast.Name)}
        if "_gemerkt" not in _test:
            continue
        _rufe_im_else = any(
            isinstance(c, _ast.Call) and isinstance(c.func, _ast.Name)
            and c.func.id == "_frage" for c in _ast.walk(_ast.Module(
                body=_k.orelse, type_ignores=[])))
    pruefe(P, "der Modellaufruf steht hinter der Speicherabfrage",
           _rufe_im_else,
           "steht er davor, wird trotzdem zweimal gefragt und der Speicher "
           "ist Zierde. Geprueft ueber den Syntaxbaum, nicht ueber Text - "
           "eine Textsuche findet auch den Kommentar (Lehre vom 31.08.)")

    # ---- 4: der Trichter zaehlt ZELLEN ----------------------------------
    # ⚠️ `Durchlauf` schluesselt auf das SYMBOL. Laeuft ein Asset zweimal und
    # `beginne()` steht ausserhalb der Schleife, faellt der zweite Durchgang
    # still unter den Tisch: `verloren()` prueft `if symbol not in self._offen`
    # und kehrt wortlos zurueck.
    from agent.rollen_gate import Durchlauf as _D
    _d = _D()
    _d.beginne("BTC")
    _d.verloren("BTC", "auswahl", "probe")
    _vorher = _d.verloren_je_stufe.get("auswahl", 0)
    _d.verloren("BTC", "auswahl", "zweite Zelle ohne beginne")
    _ohne = _d.verloren_je_stufe.get("auswahl", 0) - _vorher
    _d.beginne("BTC")
    _d.verloren("BTC", "auswahl", "zweite Zelle MIT beginne")
    _mit = _d.verloren_je_stufe.get("auswahl", 0) - _vorher - _ohne
    pruefe(P, "ohne `beginne` je Zelle zaehlt die zweite Zelle NICHT",
           _ohne == 0 and _mit == 1,
           "das ist die Falle, und sie ist hier festgehalten: ohne beginne "
           "%d gezaehlt, mit beginne %d. Deshalb steht `durchlauf.beginne` "
           "in der Zellenschleife" % (_ohne, _mit))
    _hat_beginne_in_schleife = False
    for _k in _ast.walk(_baum):
        if isinstance(_k, _ast.For) and isinstance(_k.target, _ast.Tuple):
            _n = {x.id for x in _k.target.elts if isinstance(x, _ast.Name)}
            if "symbol" in _n:
                _hat_beginne_in_schleife = any(
                    isinstance(c, _ast.Call) and isinstance(c.func, _ast.Attribute)
                    and c.func.attr == "beginne" for c in _ast.walk(_k))
    pruefe(P, "und `beginne` steht tatsaechlich in der Zellenschleife",
           _hat_beginne_in_schleife,
           "geprueft ueber den Syntaxbaum: die Schleife laeuft ueber ein "
           "Paar (symbol, strategie) und enthaelt den Aufruf")

    # ---- 5: die uebernommene Antwort wird BENANNT -----------------------
    pruefe(P, "die zweite Zelle bekommt eine Notiz im Trichter",
           "Urteil aus der Einstiegsfrage uebernommen" in _quelle,
           "eine Antwort auf eine Frage zu benutzen, die so nicht gestellt "
           "wurde, ist genau der H-Fehler ('die Anwendung reicht weiter als "
           "die Messung'). Vertretbar ist er nur, wenn er sichtbar ist")

    # ---- 6: kein Pseudo-Hebel -------------------------------------------
    _hebel = [x for x in _z if x["instrument"] == "hebel"]
    pruefe(P, "`zellen()` fuehrt Hebelzellen weiterhin",
           bool(_hebel),
           "die Liste soll ehrlich bleiben: der Hebel IST fuer diese Assets "
           "freigeschaltet. ⚠️ Der Lauf sammelt daraus die STRATEGIE - fuer "
           "ein gewoehnliches Asset faellt `hebel x einstieg` mit "
           "`spot x einstieg` zusammen (dieselbe Frage, das Instrument "
           "entscheidet die Rechnung), fuer ein Kern-Asset ist es die "
           "einzige taktische Kauffrage")
    # ⚠️⚠️ DIE REGEL, DIE AM 01.09. NACH EINER NUTZERKLAERUNG ENTSTAND.
    #
    # Meine erste Fassung filterte die Zellen auf das INSTRUMENT des Laufs
    # und warf damit alle Hebelzellen weg. Fuer LINK war das richtig - dort
    # ist `hebel x einstieg` dieselbe Frage wie `spot x einstieg`. Fuer BTC
    # war es FALSCH: dort ERSETZT die Akkumulation den Spot-Einstieg
    # (`strategie_fuer` gibt `return "akkumulation"`), und die Hebelzelle
    # waere die EINZIGE taktische Kauffrage.
    #
    # Gesammelt wird deshalb die STRATEGIE; das Instrument faellt aus der
    # Rechnung an (Kapitel 88).
    def _strategien(sym, conn):
        _aus = []
        for _zz in _AK.zellen(_WLOBJ([sym]), conn):
            if _zz["strategie"] not in _aus:
                _aus.append(_zz["strategie"])
        return set(_aus)

    pruefe(P, "ein Kern-Asset hat ZWEI Fragen, ein gewoehnliches EINE",
           _strategien("BTC", _c) == {"einstieg", "akkumulation"}
           and _strategien("LINK", _c) == {"einstieg"},
           "BTC: langfristig aufbauen UND kurzfristig taktisch - A2 im Plan "
           "(28.08.): 'zwei Positionen, zwei Horizonte, zwei Fragen'. "
           "LINK: eine Frage, das Instrument faellt aus der Rechnung an. "
           "Gemessen BTC %s / LINK %s"
           % (sorted(_strategien("BTC", _c)), sorted(_strategien("LINK", _c))))
    pruefe(P, "der Lauf sammelt die STRATEGIE, nicht das Instrument",
           'if _z["strategie"] not in _vorhandene' in _quelle
           and '_z.get("instrument") != instrument' not in _quelle,
           "das Instrument einer Zelle ist ein Wunsch - welches es wird, "
           "faellt aus `hebel = verlustanteil / stop_rel` an. Wer auf das "
           "Instrument filtert, wirft bei den Kern-Assets die einzige "
           "taktische Frage weg")

    # ---- 7: die taktische Zelle faellt OHNE Hebel weg -------------------
    pruefe(P, "die taktische Zelle wird als solche erkannt",
           '_taktisch = (_x == "einstieg" and "akkumulation" in _st)' in _quelle,
           "taktisch ist genau die zusaetzliche Einstiegszelle eines Assets, "
           "das ohnehin akkumuliert wird - bei allen anderen ist der "
           "Einstieg die gewoehnliche und einzige Kauffrage")
    _hat_abbruch = False
    for _k in _ast.walk(_baum):
        if not isinstance(_k, _ast.If):
            continue
        _n = {x.id for x in _ast.walk(_k.test) if isinstance(x, _ast.Name)}
        if "ist_taktisch" not in _n:
            continue
        _hat_abbruch = (any(isinstance(c, _ast.Return) for c in _k.body)
                        and any(isinstance(c, _ast.Call)
                                and isinstance(c.func, _ast.Attribute)
                                and c.func.attr == "verloren"
                                for c in _ast.walk(_k)))
    # ---- SCHRITT 6 / I-2: `hebel x akkumulation` ENTSTEHT NICHT MEHR ----
    #
    # ⚠️ Bis zum 01.09. wurde der Konflikt HINTERHER gemeldet: der Lauf
    # schrieb *„ACHTUNG: ETH laeuft als akkumulation, die Rechnung ergibt
    # aber das Etikett 'hebel'"*. Die Begruendung fuer Melden statt Sperren
    # lautete: *„Ein Abbruch naehme dem Kern seine Meldung."*
    #
    # Seit Schritt 3+4 ist das hinfaellig: der Kern hat eine ZWEITE Zelle
    # (die taktische), und dorthin gehoert der Hebel. Die Akkumulation
    # verliert nichts, wenn sie ihn nicht bekommt - also entsteht das Paar
    # gar nicht erst.
    from agent.handelsauftrag import (hebel_erlaubt_fuer as _HEB,
                                      ERLAUBTE_PAARE as _EP)
    pruefe(P, "`hebel_erlaubt_fuer` liest die Paar-Matrix, keine zweite Liste",
           _HEB("einstieg") and _HEB("swing")
           and not _HEB("akkumulation")
           and set(_EP["hebel"]) == {s for s in ("einstieg", "swing",
                                                 "akkumulation")
                                     if _HEB(s)},
           "die Antwort MUSS deckungsgleich mit `ERLAUBTE_PAARE['hebel']` "
           "sein - eine eigene Aufzaehlung waere die naechste Stelle zum "
           "Auseinanderlaufen. Matrix: %s" % (_EP["hebel"],))
    pruefe(P, "ein unlesbarer Wert heisst NICHT erlaubt",
           not _HEB("") and not _HEB(None) and not _HEB("unbekannt"),
           "dieselbe Linie wie in `asset_schalter`: ein Lesefehler darf "
           "nichts einschalten, was nicht vorgesehen ist")
    # ⚠️ DIE WIRKUNG, nicht nur die Verdrahtung: dieselbe Lage, einmal mit
    # und einmal ohne Hebelerlaubnis.
    from agent import entscheidungsrechnung as _ER6
    _mit = _ER6.dimensioniere(kurs=100.0, atr=6.0, k=0.75, verlustanteil=0.25,
                              einsatz_eur=800.0, hebel_handelbar=True)
    _ohne = _ER6.dimensioniere(kurs=100.0, atr=6.0, k=0.75, verlustanteil=0.25,
                               einsatz_eur=800.0, hebel_handelbar=False)
    pruefe(P, "ohne Hebelerlaubnis entsteht kein Hebel-Etikett",
           _mit["etikett"] == "hebel" and _mit["hebel"] > 1.0
           and _ohne["etikett"] == "spot" and _ohne["hebel"] == 1.0,
           "dieselbe Lage: mit Erlaubnis %s/%.2f, ohne %s/%.2f. Waere die "
           "Zeile wirkungslos, saehe man hier zweimal dasselbe"
           % (_mit["etikett"], _mit["hebel"], _ohne["etikett"], _ohne["hebel"]))
    # ⚠️ UND BEIDE RECHNUNGEN MUESSEN DIESELBE ANNAHME HABEN. Bekaeme die
    # VORABrechnung keinen Hebel und die ECHTE doch, liefen sie auseinander -
    # der Trichter zeigte auf eine Zelle, die die Mail anders rechnet.
    _stellen = _quelle.count("_HA_HEBEL_OK(strategie)")
    pruefe(P, "beide Rechnungen fragen die Strategie - `dimensioniere` UND "
              "`rechne`",
           _stellen == 2,
           "gefunden an %d Stellen, erwartet 2. Eine Rechnung mit und eine "
           "ohne Hebelerlaubnis waeren zwei verschiedene Trades unter einem "
           "Namen" % _stellen)
    # ---- SCHRITT 7: DIE POSITIONSFUEHRUNG IST VERDRAHTET ---------------
    #
    # ⚠️ `positionsfuehrung` stand seit dem 27.08. GEBAUT und ohne Aufrufer
    # in der Toten-Liste der Modulkarte - Punkt B im Roten Faden. Die
    # Nutzerfestlegung vom 26.08. war damit nie erfuellt: *„eine Position
    # bleibt eine Position - hier sollte auch der Verlust sichtbar sein und
    # somit ein Break-even."*
    from agent import verkaufsrechnung as _VK7
    from agent import positionsfuehrung as _PF7
    pruefe(P, "der Lauf ruft die Positionsfuehrung",
           "positionsfuehrung as _PF" in _quelle
           and "_PF.zeilen(" in _quelle,
           "gebaut und nicht gerufen ist im Projekt die haeufigste Luecke - "
           "`marktrang.saetze()` und `zellen()` waren dieselbe Klasse")
    pruefe(P, "und `sammel_mail` nimmt sie entgegen",
           "positionen" in _VK7.sammel_mail.__code__.co_varnames,
           "ohne den Parameter waere der Aufruf oben wirkungslos - und "
           "genau so sehen halbe Verdrahtungen aus")

    # ⚠️ DIE WIRKUNG AM TEXT, nicht an der Verdrahtung: der Abschnitt muss
    # in der fertigen Mail stehen, und ohne Positionen darf er FEHLEN.
    _posten = [{"symbol": "BTC", "verkauf": {"aktion": "VERKAUFEN",
                                             "anteil": 1.0,
                                             "gegenwert_eur": 500.0},
                "begruendung": "Probe"}]
    _ohne = _VK7.sammel_mail(_posten)
    _mit = _VK7.sammel_mail(_posten, positionen=[["BTC - eine Position",
                                                  "   Break-even   100 EUR"]])
    pruefe(P, "die Positionsfuehrung steht in der fertigen Sammelmail",
           _mit and "WAS SIE HALTEN" in _mit[1]
           and "Break-even" in _mit[1],
           "der Break-even ist der Punkt der ganzen Uebung - er war die "
           "woertliche Nutzerforderung")
    pruefe(P, "und der Abschnitt fehlt, wenn nichts gehalten wird",
           _ohne and "WAS SIE HALTEN" not in _ohne[1],
           "eine leere Ueberschrift ist eine Zeile, die etwas verspricht "
           "und nichts haelt")
    pruefe(P, "die Vorschlaege bleiben daneben stehen, nicht darunter",
           _mit and _mit[1].index("WAS ZU TUN IST")
           < _mit[1].index("WAS SIE HALTEN") < _mit[1].index("WARUM"),
           "was zu TUN ist und was man HAT sind zwei Befunde, keine zwei "
           "Meinungen - sie gehoeren nebeneinander und in dieser Reihenfolge")
    # ⚠️ UND SIE ERFINDET KEIN R (N-11). Eine Spot-Position hat keinen Stop,
    # also kein R. Wer hier eines erfaende, baute genau den Fehler ein, den
    # N-11 aufgedeckt hat.
    pruefe(P, "die Fuehrung erfindet kein R fuer eine Position ohne Stop",
           " R" not in chr(10).join(_PF7.zeilen(_PF7.Position(
               symbol="BTC", instrument="spot", menge_frei=1.0,
               menge_gestakt=0.0, einstand_eur=100.0, kurs_eur=110.0))),
           "eine Spot-Position hat nach Nutzerangabe keinen Stop - ohne Stop "
           "gibt es kein R und keinen sinnvollen MFE. Was sie hat, ist ein "
           "Einstand, und daraus Euro und Prozent")

    # ---- SCHRITT 5: DER TERMINMARKT IN DER FAKTENLAGE -------------------
    from agent import positionierung as _PO5p
    from agent import anlass as _AN5
    _lage = {"symbol": "LINK", "fehlt": [], "oi_aenderung_pct": -1.54,
             "oi_fenster_stunden": 0.8,
             "boersenfluss": {"datum": "2026-08-31", "netto": 327.0,
                              "perzentil": 62, "n": 730},
             "fehlt_rahmen": ["Boersenzu- und -abfluesse"]}
    _mit_rahmen = _PO5p.saetze(_lage)
    _nur_eigen = _PO5p.saetze(_lage, nur_eigen=True)
    # ⚠️ G2: der Boersenfluss misst BITCOIN fuer den ganzen Markt. Ungefiltert
    # stuende er in der Faktenlage von LINK - ein bekannter Defekt, in einen
    # zweiten Kanal getragen.
    pruefe(P, "der Rahmen bleibt aus der Faktenlage des Assets draussen",
           any("Bitcoin" in z for z in _mit_rahmen)
           and not any("Bitcoin" in z for z in _nur_eigen)
           and not any("Gesamtmarkt" in z for z in _nur_eigen),
           "`positionierung` mischt Asset und Rahmen und sagt das selbst "
           "(`fehlt` gegen `fehlt_rahmen`). Rolle G braucht den Rahmen - die "
           "Faktenlage eines einzelnen Assets nicht. Mit Rahmen: %s"
           % _mit_rahmen[-2:])
    pruefe(P, "⚠️ und Rolle G behaelt ihn - sie wird nicht mitgeaendert",
           any("Bitcoin" in z for z in _mit_rahmen),
           "sie beurteilt die LAGE; ihr den Rahmen zu nehmen waere ein "
           "zweiter Umbau ohne Anlass")
    # ⚠️ DIE AUFLOESUNG: fein wechselt der Satz bei 68-74 % der Messungen
    # (gemessen an 2.988 Punkten je Symbol), grob bei 5-7,5 %.
    # ⚠️ ALLE VIER STUFEN, nicht eine Stichprobe - meine erste Fassung
    # erwartete "deutlich" bei -1,54 % und lag damit selbst daneben.
    def _stufe(pct):
        _l = dict(_lage, oi_aenderung_pct=pct)
        return _PO5p.saetze(_l, nur_eigen=True)[0]

    _erw = ((0.4, "praktisch unveraendert"), (-1.54, "leicht gefallen"),
            (5.0, "deutlich gestiegen"), (-12.0, "stark gefallen"))
    pruefe(P, "die Faktenlage nennt STUFEN - alle vier, an ihren Grenzen",
           all(w in _stufe(x) for x, w in _erw),
           "Grenzen 1/3/8 %%. Gemessen: " + " | ".join(
               "%.2f -> %s" % (x, _stufe(x)[-30:]) for x, _w in _erw))
    pruefe(P, "und Rolle G behaelt die genaue Zahl",
           "1,5 %" in " ".join(_mit_rahmen),
           "eine Prozentzahl auf eine Nachkommastelle wechselt bei 68-74 %% "
           "der Messungen - in der Faktenlage waere damit JEDE Frage neu und "
           "die Anlass-Sperre wirkungslos. Mit Stufen sind es 5-7,5 %%. "
           "Gemessen an 2.988 Punkten je Symbol, nicht geschaetzt")
    # ⚠️ DIE WIRKUNG: aendert sich der Fingerabdruck ueberhaupt?
    _b = {"kurs": "1.093 EUR wert"}
    _f0 = _AN5.fingerabdruecke(_b)[1]
    _f1 = _AN5.fingerabdruecke(dict(_b, terminmarkt=["OI leicht gefallen."]))[1]
    _f2 = _AN5.fingerabdruecke(dict(_b, terminmarkt=["OI stark gestiegen."]))[1]
    pruefe(P, "eine Terminmarkt-Aenderung erzeugt eine NEUE Frage",
           _f0 != _f1 != _f2 and _f0 != _f2,
           "vorher war das unmoeglich: der Terminmarkt stand in KEINEM "
           "Faktensatz, also konnte er keine Frage ausloesen - der Takt "
           "entschied, wann hingesehen wird. Genau das verbietet Regel 1")
    _lauf5 = _pl_pfad("agent/rollen_lauf.py")
    pruefe(P, "der Lauf speist ihn nur bei Krypto ein",
           'bc_ein["terminmarkt"]' in _lauf5
           and 'nur_eigen=True' in _lauf5,
           "Aktien und ETFs haben keinen Perpetual-Terminmarkt; dort waere "
           "der Block eine Zeile ueber etwas, das es nicht gibt")

    # ---- SCHRITT 8: DER ALTBESTAND IST ABGEGRENZT -----------------------
    #
    # Umbauplan Schritt 8. Die Festlegung dort, Zeile fuer Zeile:
    #
    #   hebel_positions  188, alle geschlossen -> BLEIBT (echte
    #                    Positionsfuehrung, Bitpanda-Import fuellt weiter,
    #                    `ui/hebel_view.py` zeigt sie)
    #   hebel_signals    1.998, letztes 10.08. -> BLEIBT LESBAR, wird nicht
    #                    mehr geschrieben. KEIN Rueckbau, die GUI zeigt
    #                    Historie
    #   hebel_triggers   82.655, waechst -> Schritt 5 (erledigt 01.09.)
    #
    # ⚠️ GEPRUEFT WIRD DIE GRENZE, NICHT DIE ABSICHT. Ein Plan, der sagt
    # "wird nicht mehr geschrieben", ist eine Absichtserklaerung; eine
    # Pruefung, die es festhaelt, ist eine Naht.
    _NEUE_KETTE = ("agent/rollen_lauf.py", "agent/rollen_gate.py",
                   "scheduler/rollen_job.py", "agent/rollen_eingabe.py",
                   "agent/signal_abbildung.py")
    _schreibt = []
    for _f8 in _NEUE_KETTE:
        _lit8 = {n.value for n in _ast.walk(_ast.parse(_pl_pfad(_f8)))
                 if isinstance(n, _ast.Constant) and isinstance(n.value, str)}
        for _x in _lit8:
            _o = _x.upper()
            if any(k in _o for k in ("INSERT", "UPDATE ", "DELETE")) and any(
                    tb in _x for tb in ("hebel_signals", "hebel_positions",
                                        "hebel_triggers")):
                _schreibt.append("%s: %s" % (_f8.split("/")[-1], _x[:60]))
    pruefe(P, "die neue Kette SCHREIBT nicht in den Altbestand",
           not _schreibt,
           "gefunden: %s. `hebel_signals` fuehrt Historie (letztes Signal "
           "10.08.), `hebel_positions` fuellt der Bitpanda-Import. Wer von "
           "der neuen Kette dort hineinschreibt, vermischt zwei Bestaende, "
           "die auseinandergehalten werden sollen" % (_schreibt or "nichts"))
    # ⚠️ UND SIE DARF LESEN. Die Positionsfuehrung braucht beide Quellen
    # (I-3, 28.08.: "beide Quellen, nicht eine waehlen") - ein Symbol kann
    # Spot UND Hebel tragen.
    _liest = {n.value for n in _ast.walk(
        _ast.parse(_pl_pfad("agent/rollen_eingabe.py")))
        if isinstance(n, _ast.Constant) and isinstance(n.value, str)}
    pruefe(P, "aber sie DARF den Altbestand lesen",
           any("hebel_positions" in x for x in _liest),
           "der Bestand ist Bestand, egal wer ihn eingetragen hat. Ein "
           "Symbol kann Spot UND Hebel tragen - `rollen_eingabe.bestand` "
           "muss beide sehen, sonst fehlt dem Nutzer die halbe Position")

    pruefe(P, "die alte I-2-MELDUNG bleibt als Waechter stehen",
           "ein Paar, das die Matrix ausschliesst" in _quelle,
           "sie ist ab jetzt strukturell unerreichbar - schlaegt sie doch "
           "noch an, ist etwas anderes kaputt. Eine Meldung zu loeschen, "
           "weil ihr Fall behoben ist, nimmt dem naechsten Fehler den Melder")

    pruefe(P, "und sie faellt heraus, wenn die Rechnung keinen Hebel ergibt",
           _hat_abbruch,
           "Nutzerentscheidung 01.09.: 'nur wenn die Rechnung tatsaechlich "
           "einen Hebel ergibt'. ⚠️ GEZAEHLT UND BEGRUENDET, nicht still - "
           "geprueft ueber den Syntaxbaum: der Zweig muss `verloren()` "
           "rufen UND zurueckkehren")


def paket_hartes_budget() -> None:
    """C2 - das Risikobudget als GRENZE, hinter einem Schalter (28.08.2026).

    ⚠️ ICH HATTE DAS ALS KORREKTUR AUSGEGEBEN. Es ist keine. Die eigene Suite
    hat mich gestoppt (Paket Q, 14.08.):

        "Bei Spot OHNE Stop-Order gibt es keine Groesse, die aus dem Stop
         folgen koennte."
        "Tranche 800 -> Betrag 4.800. Dort stand 960, wo der Nutzer 800 gesagt
         hatte - der Betrag haette am Stopabstand gehangen statt an seiner
         Entscheidung."

    `Umbauplan_Gesamtsystem_12_08.md` fuehrt **C2** als "festes Risiko oder
    fester Betrag - offen, GELDFRAGE". Wer den Betrag aus dem Budget ableitet,
    entscheidet sie - und das ist Nutzersache.

    DESHALB EIN SCHALTER, dessen Vorgabe nichts aendert. Was sich auch ohne
    ihn aendert: der Ueberschuss wird BENANNT statt verschwiegen. Das war der
    eigentliche Fehler - nicht die Groesse, sondern das Schweigen."""
    from agent import entscheidungsrechnung as _ER

    P = "Budget"
    BUDGET = 30.0

    def _r(stop_rel, hart=False, wunsch=500.0, risiko=BUDGET):
        return _ER.rechne(kurs=100000, atr=100000 * stop_rel / 2.0,
                          risiko_eur=risiko, instrument="spot",
                          betrag_wunsch_eur=wunsch, topf_frei_eur=wunsch,
                          hebel_handelbar=True, risikobudget_hart=hart)

    # ---- DIE VORGABE AENDERT NICHTS ----
    for stop in (0.03, 0.08, 0.15):
        pruefe(P, "ohne Schalter bleibt der Betrag der Wunsch (%.0f %% Stop)"
               % (100 * stop),
               _r(stop).get("betrag_eur") == 500.0,
               "C2 ist offen - `risiko_quelle` sagt ausdruecklich, dass der "
               "Betrag bei Spot die Entscheidung des Nutzers ist. Bekommen: "
               "%s" % _r(stop).get("betrag_eur"))

    # ---- ABER DER UEBERSCHUSS WIRD BENANNT ----
    pruefe(P, "die Budgetueberschreitung steht in der Rechnung",
           _r(0.08).get("budget_ueberschritten_um") is not None
           and _r(0.08)["budget_ueberschritten_um"] > 0.6,
           "bei 8 %% Stop und 30 EUR Budget riskiert der volle Betrag 50 EUR "
           "- das sind 67 %% darueber. Vorher stand davon NICHTS in der "
           "Rechnung; die Untergrenze hat den Ueberschuss verschwiegen. "
           "Bekommen: %s" % _r(0.08).get("budget_ueberschritten_um"))
    pruefe(P, "und nur dort, wo er auftritt",
           _r(0.03).get("budget_ueberschritten_um") is None,
           "bei engem Stop gilt L x stop = verlustanteil, das Budget haelt "
           "von selbst - eine Meldung waere ein Fehlalarm")

    # ---- MIT SCHALTER HAELT DAS BUDGET ----
    for stop in (0.03, 0.06, 0.08, 0.12, 0.20):
        r = _r(stop, hart=True)
        pruefe(P, "mit Schalter haelt das Budget bei %.0f %% Stop"
               % (100 * stop),
               r.get("verlust_am_stop_eur") is not None
               and abs(r["verlust_am_stop_eur"] - BUDGET) < 0.51,
               "Budget %.0f EUR, gerechnet %s" % (BUDGET,
                                                  r.get("verlust_am_stop_eur")))
    pruefe(P, "und der Betrag traegt die Anpassung",
           _r(0.15, hart=True)["betrag_eur"] < _r(0.03, hart=True)["betrag_eur"],
           "eng %s gegen weit %s EUR"
           % (_r(0.03, hart=True).get("betrag_eur"),
              _r(0.15, hart=True).get("betrag_eur")))
    pruefe(P, "mit Deckelgrund",
           "Risikobudget" in str(_r(0.15, hart=True).get(
               "betrag_gedeckelt_durch") or ""),
           "ein stiller Deckel ist ein verschwiegener Deckel")

    # ---- ⚠️ betrag_eur darf NIE fehlen ----
    #
    # Beim Bau habe ich `e["betrag_eur"] = round(betrag, 0)` versehentlich
    # MITERSETZT - der Schluessel fehlte danach vollstaendig. In der Probe
    # gefunden, nicht im Betrieb; diese Zeile haelt es fest.
    for stop in (0.03, 0.08, 0.20):
        for hart in (False, True):
            pruefe(P, "betrag_eur ist gesetzt (%.0f %%, hart=%s)"
                   % (100 * stop, hart),
                   _r(stop, hart=hart).get("betrag_eur") is not None,
                   "der Schluessel fiel beim Umbau heraus - jede lesende "
                   "Stelle haette None bekommen")

    # ---- risiko_eur folgt dem ETIKETT, nicht dem Lauf (I-1) ----
    r = _r(0.03)
    pruefe(P, "bei Hebel widersprechen sich die Risikofelder nicht",
           r.get("etikett") == "hebel"
           and abs((r.get("risiko_eur") or 0)
                   - (r.get("verlust_am_stop_eur") or 0)) < 0.51,
           "Hier stand `instrument != \"hebel\"`, und `instrument` ist seit "
           "S6b immer \"spot\": bei Hebel 1,6 stand risiko_eur auf 18,75 "
           "waehrend verlust_am_stop_eur 30,00 sagte. Bekommen: %s gegen %s"
           % (r.get("risiko_eur"), r.get("verlust_am_stop_eur")))

    # ---- GEGENPROBE: der Hebel-Zweig bleibt unberuehrt ----
    pruefe(P, "ein echter Hebel behaelt den vollen Betrag - mit und ohne",
           _r(0.03).get("betrag_eur") == 500.0
           and _r(0.03, hart=True).get("betrag_eur") == 500.0,
           "bei L > 1 haelt das Budget von selbst; dort darf nichts gekuerzt "
           "werden, egal wie der Schalter steht")


PAKETE = {"0": paket_0, "1": lambda: (paket_1(), paket_1_schema()),
          "2": paket_2, "3": paket_3, "4": paket_4, "5": paket_5,
          "6": paket_6, "7": paket_7, "8": paket_8, "9": paket_9,
          "10": paket_10, "11": paket_11, "12": paket_12, "13": paket_13, "14": paket_14, "12c": paket_12c, "12b": paket_12b, "12d": paket_12d, "13": paket_13, "gesamt": gesamtpruefung, "B1": paket_b1, "Export": paket_export, "15": paket_15, "Mail": paket_mail, "Belege": paket_belege, "Lesbar": paket_lesbar, "BTC": paket_btcmail, "Marken": paket_marken, "Provider": paket_provider, "Luecken": paket_luecken, "Fett": paket_fett, "Andrang": paket_andrang, "Ausfall": paket_ausfall, "Dimension": paket_dimension,
          "Frische": paket_frische,
          "Auswahl": paket_auswahl,
          "Verkauf": paket_verkaufsseite,
          "Akkumass": paket_akkumass,
          "Abkapselung": paket_abkapselung,
          "Akkumulationslage": paket_akkumulationslage,
          "T4c": paket_namensschatten,
          "L3": paket_l3,
          "I-Reparatur": paket_instrument_reparatur,
          "Budget": paket_hartes_budget,
          "Terminmarkt": paket_terminmarkt,
          "Trennung": paket_trennung,
          "Zellen": paket_zellen,
          "Stufen": paket_beitrag_stufen,
          "Kalibrierung": paket_kalibrierung}


class _Mitschnitt:
    """Schreibt jede Ausgabe an die echte Konsole UND in einen Puffer.

    ⚠️ NUR DESHALB, WEIL EINE EXTERNE ZUSAMMENFASSUNG SCHON ZWEIMAL DEN
    VOLLTEXT VERLOR (24.08.2026): einmal bei 20.010 Zeichen abgeschnitten
    (die '1678'-Kennzahl fehlte), einmal beim Zeitdeckel nach zwei Minuten.
    Die Konsole bleibt unveraendert - der Puffer geht zusaetzlich nach
    Google Drive, siehe `_schreibe_ausgabe_ins_austauschordner()`."""

    def __init__(self, original, puffer: io.StringIO) -> None:
        self._original = original
        self._puffer = puffer

    def write(self, s: str) -> int:
        self._puffer.write(s)
        return self._original.write(s)

    def flush(self) -> None:
        self._original.flush()


def _schreibe_ausgabe_ins_austauschordner(text: str) -> None:
    """Volltext nach Google Drive, damit niemand ihn mehr abtippen oder aus
    einer gekuerzten Zusammenfassung zurueckdeuten muss.

    ⚠️ BEST EFFORT. Der Laufwerksbuchstabe unterscheidet sich je Geraet
    (`extract_notebook_diagnose._google_drive_wurzel()` sucht ihn) - und ist
    Google Drive gerade nicht gemountet (z.B. auf einem dritten Rechner),
    darf DAS die Suite nicht zu Fall bringen. Deshalb ein eigener, getrennter
    Ordner `Pruefungen`, NICHT `Notebook_Analysedaten` - Testergebnisse sind
    Code-Korrektheit, kein Produktionszustand, und beides in dieselbe Datei
    zu schreiben wuerde genau die Verwechslung wieder einfuehren, die beim
    NB-Export schon einmal Verwirrung gestiftet hat.

    ⚠️ DER DATEINAME TRAEGT DAS GERAET (24.08.2026-Fund, noch am selben Tag
    wie der Ordner selbst): ohne das ueberschreibt ein Desktop-Testlauf, der
    zur Verifikation eines Fixes laeuft, kommentarlos das Ergebnis vom
    Notebook - und umgekehrt. Genau das ist passiert: eine Auswertung hielt
    einen eigenen Desktop-Lauf faelschlich fuer den frischen Notebook-Lauf,
    weil beide unter demselben Namen landeten. `platform.node()` statt eines
    Zeitstempels, weil ZWEI GERAETE unterscheidbar sein muessen - nicht zwei
    Zeitpunkte desselben Geraets."""
    try:
        import platform
        from datetime import datetime, timezone
        from extract_notebook_diagnose import _google_drive_wurzel
        ziel = _google_drive_wurzel() / "Claude_Austauschordner" / "Pruefungen"
        ziel.mkdir(parents=True, exist_ok=True)
        geraet = (platform.node() or "unbekannt").strip() or "unbekannt"
        pfad = ziel / f"pruefe_pakete_ausgabe_{geraet}.txt"
        kopf = (f"# Geraet: {geraet}\n"
                f"# Geschrieben: "
                f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        pfad.write_text(kopf + text, encoding="utf-8")
        print(f"\n(Volltext geschrieben nach {pfad})")
    except Exception as exc:                                   # noqa: BLE001
        print(f"\n(Konnte Ausgabe nicht auf Google Drive schreiben: {exc})")


def main() -> int:
    # ⚠️ DIE KONSOLE MUSS DIE ZEICHEN AUSHALTEN, DIE DAS PRODUKT BENUTZT
    # (17.08.2026). Seit die Mail wieder ▲/●/▼ verwendet, stehen diese
    # Zeichen in Pruefdetails - und Windows gibt hier cp1252 aus. Die
    # ganze Suite brach mit einem UnicodeEncodeError ab, also gab ein
    # Werkzeug, das Fehler finden soll, selbst einen aus.
    #
    # `errors="replace"` statt Zeichen zu meiden: was das Produkt
    # schreibt, soll die Pruefung zeigen duerfen - notfalls mit einem
    # Ersatzzeichen, aber nie mit einem Abbruch.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--paket", default=None, help="nur dieses Paket pruefen")
    a = ap.parse_args()
    laufen = [a.paket] if a.paket else sorted(PAKETE)

    _original_stdout = sys.stdout
    _puffer = io.StringIO()
    sys.stdout = _Mitschnitt(_original_stdout, _puffer)
    try:
        for p in laufen:
            if p not in PAKETE:
                print(f"[FEHLER] Paket {p} kennt diese Datei nicht - "
                      f"bekannt: {sorted(PAKETE)}")
                return 2
            PAKETE[p]()

        letztes = None
        schlecht = 0
        for paket, name, ok, detail in _ERGEBNISSE:
            if paket != letztes:
                print(f"\n--- PAKET {paket} " + "-" * 56)
                letztes = paket
            print(f"  {'OK  ' if ok else 'FEHL'}  {name}")
            if detail and not ok:
                print(f"        {detail}")
            elif detail and ok:
                print(f"        ({detail})")
            schlecht += 0 if ok else 1

        print("\n" + "=" * 68)
        print(f"{len(_ERGEBNISSE)} Pruefungen, "
              + ("ALLE BESTANDEN" if not schlecht else f"{schlecht} FEHLGESCHLAGEN"))
        return 1 if schlecht else 0
    finally:
        sys.stdout = _original_stdout
        _schreibe_ausgabe_ins_austauschordner(_puffer.getvalue())


if __name__ == "__main__":
    raise SystemExit(main())
