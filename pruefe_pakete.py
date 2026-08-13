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

Kein LLM-Aufruf, kein Netzwerk, keine Schreibzugriffe. Diese Datei darf jederzeit
laufen.
"""
from __future__ import annotations

import argparse
import io
import re
import sys

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
    pruefe(P, "die Makrolage steht VOR dem ersten Leitmarkt",
           alle[:2] == saetze,
           f"{len(alle)} Aussagen; Makro rahmt alle drei Maerkte zugleich")


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
    pruefe(P, "Spot wird nicht doppelt gedeckelt",
           T.budget_eur("spot", cfg) is None,
           "die RM-Regeln begrenzen die Einzelposition bereits")
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
    pruefe(P, "alle Reihen liegen in USD - der ATR also auch",
           set(w.values()) == {"USD"}, str(set(w.values())))
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
    pruefe(P, "1.500 EUR Wunsch kommen nicht durch",
           e["betrag_eur"] <= 500 and e["betrag_gedeckelt_durch"] == "Topf",
           "der Topf ist ein Deckel, kein Richtwert")
    a, regel = ER._stop_abstand(55500, 1677, 54800)
    pruefe(P, "ein 1,26-%-Stop kommt nicht durch",
           a / 55500 >= ER.GRENZEN["stop_min_relativ"] and "Rauschen" in regel,
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
    for nr, name in ((1, "DER COIN"), (2, "DIE RECHNUNG"),
                     (3, "DAS URTEIL DES MODELLS"), (4, "EINORDNUNG")):
        pruefe(P, f"Abschnitt {nr} heisst '{name}'", f"--- {nr}. {name} ---" in text)
    pruefe(P, "der Coin steht VOR der Rechnung",
           text.index("1. DER COIN") < text.index("2. DIE RECHNUNG"),
           "Nutzer: 'Info Teil zum Coin und dann die wichtigen Abschnitte'")
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
    con3.close()
    pruefe(P, "jedes Signal MIT Gate traegt seine Fakten",
           verletzt == 0,
           "die 78 leeren sind Abweisungen VOR der Analyse - dort gab es nie "
           "Fakten. Meine erste Meldung ('Defekt') war eine Zahl ohne ihre "
           "Schichtung")
    pruefe(P, "und die leeren sind alle Abweisungen",
           leer_ohne_gate == 78, f"{leer_ohne_gate} statt 78")

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
    falsch = lauf(kurs_aktuell=50900, umgeworfen_preis_eur=51000)
    pruefe(P, "ein erreichter Widerlegungspreis fuehrt zu SCHLIESSEN",
           falsch["falsifiziert"] and falsch["empfehlung"] == AR.SCHLIESSEN,
           "die Fakten-Entscheidungsmappe: 'heute von niemandem ausgewertet'")
    pruefe(P, "ein NICHT erreichter nicht",
           lauf(kurs_aktuell=56000, umgeworfen_preis_eur=51000)["falsifiziert"] is False)
    pruefe(P, "faellt er mit dem Stop zusammen, wird das gesagt",
           falsch["falsifikator_eigenstaendig"] is False
           and any("beide sagen dasselbe" in g for g in falsch["gruende"]),
           "in der neuen Kette wird der Stop AUS diesem Preis abgeleitet - "
           "dann ist die Pruefung keine zweite Absicherung")
    eigen = lauf(kurs_aktuell=52000, umgeworfen_preis_eur=52500)
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
           lauf(kurs_aktuell=50900, umgeworfen_preis_eur=51000,
                umgeworfen_bis="2026-08-01")["empfehlung"] == AR.SCHLIESSEN)

    # WAS NICHT PRUEFBAR IST, WIRD NICHT BEHAUPTET.
    text = " ".join(AR.saetze(lauf(
        umgeworfen_durch="Ein Tagesschluss unter 51.000 EUR bei steigendem Volumen.")))
    pruefe(P, "die Prosa-Bedingung wird gezeigt, nicht ausgewertet",
           "Selbst zu pruefen" in text and "nicht automatisch ausgewertet" in text,
           "'bei steigendem Volumen' ist nicht zuverlaessig maschinell pruefbar")

    # SHORT.
    kurz = AR.bewerte(einstieg=100.0, stop_original=110.0, kurs_aktuell=112.0,
                      ist_short=True, umgeworfen_preis_eur=111.0, heute="2026-08-13")
    pruefe(P, "bei SHORT faellt die These nach OBEN",
           kurz["falsifiziert"] is True)
    pruefe(P, "und bei LONG nicht bei demselben Kurs",
           AR.bewerte(einstieg=100.0, stop_original=90.0, kurs_aktuell=112.0,
                      umgeworfen_preis_eur=111.0, heute="2026-08-13")["falsifiziert"] is False)

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
    _c.execute("DELETE FROM signals"); _c.execute("DELETE FROM price_cache")
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

    pruefe(P, "der MFE kommt aus dem Backward-Tracking",
           len(_r["alle"]) == 5
           and abs(_nach["BTC"]["mfe_r"] - 1.8) < 1e-9,
           "`outcome_max_realisiertes_crv` wird seit 02.08. auch fuer OFFENE "
           "Signale fortgeschrieben - er muss nicht neu gerechnet werden")
    pruefe(P, "auch Positionen UNTER der Ausloeseschwelle werden geprueft",
           "ETH" in _nach and _nach["ETH"]["mfe_r"] < 1.0,
           "vorher stand dort ein `continue` - eine Position im Minus loest "
           "den Trailing-Stop per Definition nicht aus, und genau dort ist "
           "der Widerlegungspreis am wichtigsten")
    pruefe(P, "und ihr Widerlegungspreis greift",
           _nach["ETH"]["empfehlung"] == AR.SCHLIESSEN)
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
    _c.execute("DELETE FROM signals"); _c.execute("DELETE FROM price_cache")
    _c.execute("DELETE FROM holdings")
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
    pruefe(P, "ein faelliger Ausstieg steht im BETREFF",
           betreff.startswith("TradingInfoTool: BTC - SCHLIESSEN"), betreff,)

    ruhig = lauf(kurs_aktuell=62000, hoechstkurs=ein + 1.8 * 4500)
    _, txt2 = _SM.baue_mail(symbol="BTC", name="B", kurs_eur=62000,
                            instrument="hebel", strategie="swing", rechnung=_r,
                            ausstieg=ruhig, urteil={"aktion": "NACHKAUFEN"})
    pruefe(P, "sonst stehen Bestand UND Nachkauf getrennt nebeneinander",
           "Bestehende Position:" in txt2 and "Zusaetzlicher Einstieg:" in txt2)
    pruefe(P, "und der Abschnitt heisst dann DIE POSITION",
           "--- 2. DIE POSITION ---" in txt2,
           "bei einem Bestand ist die dringendere Frage, was mit ihm "
           "geschieht - nicht, ob man noch mehr davon kauft")

    # EINE SCHREIBWEISE.
    zahlen = " ".join(AR.saetze(lauf(kurs_aktuell=50900,
                                     umgeworfen_preis_eur=50901,
                                     hoechstkurs=ein + 1.8 * 4500)))
    pruefe(P, "alle Betraege in deutscher Schreibweise",
           "50.901,00" in zahlen and "50,901.00" not in zahlen,
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
    pruefe(P, "der Entscheider zaehlt, aber nimmt nichts heraus",
           d.verloren_je_stufe["entscheider"] == 7 and d.heraus == 7,
           "'Was diese Datei nicht tut: sie verwirft nichts' - ein Waechter, "
           "der selbst verwirft, macht seine eigene Wirkung unsichtbar")
    pruefe(P, "eine echte Stufe nimmt sehr wohl heraus",
           d.verloren_je_stufe["fakten"] == 3 and d.hinein == 10)

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
    erst = RG.migriere(_c)
    zweit = RG.migriere(_c)
    pruefe(P, "die Migration legt die Tabelle an und ist idempotent",
           erst and not zweit, f"{erst} / {zweit}")
    kennung = RG.schreibe(_c, d, "2026-08-13T07:00:00+00:00")
    zeile = _c.execute(f"SELECT hinein, heraus FROM {RG.TABELLE} WHERE id=?",
                       (kennung,)).fetchone()
    pruefe(P, "und der Lauf laesst sich nachlesen", zeile == (10, 7), str(zeile))
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
           any("Z-1" in z for z in mit) and any("62.0" in z for z in mit))
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

    # DAS VOKABULAR IST DAS DER ALTEN KETTE - sonst braeuchte es eine
    # Abbildung, und jede Abbildung ist eine Stelle zum Auseinanderlaufen.
    pruefe(P, "die sieben Hebel-Aktionen sind die der alten Kette",
           set(AKTIONEN_HEBEL) == set(REQUIRED_HEBEL_ACTIONS),
           f"neu {sorted(AKTIONEN_HEBEL)} gegen alt {sorted(REQUIRED_HEBEL_ACTIONS)}")
    pruefe(P, "Spot behaelt seine fuenf", len(aktionen_fuer("spot")) == 5
           and set(aktionen_fuer("spot")) == set(AKTIONEN))
    pruefe(P, "und Hebel hat sieben", len(aktionen_fuer("hebel")) == 7)

    basis = {"begruendung": "x", "was_dagegen": "y", "umgeworfen_durch": "z"}

    # DIE RICHTUNG IST PFLICHT, WO SIE ETWAS BEDEUTET - und nur dort.
    ok = validiere({**basis, "aktion": "ERÖFFNEN", "richtung": "short",
                    "tranche_eur": 300}, "BTC", "hebel")
    pruefe(P, "ERÖFFNEN mit Richtung wird angenommen und vereinheitlicht",
           ok["aktion"] == "ERÖFFNEN" and ok["richtung"] == "SHORT")
    for aktion in ("ERÖFFNEN", "NACHKAUFEN"):
        try:
            validiere({**basis, "aktion": aktion, "tranche_eur": 300}, "BTC", "hebel")
            fehlt = False
        except EmpfehlungUngueltig:
            fehlt = True
        pruefe(P, f"{aktion} OHNE Richtung wird abgewiesen", fehlt,
               "bei der Tranche ist die kleinste Groesse die vorsichtige "
               "Antwort - bei der Richtung gibt es keine: LONG statt SHORT "
               "ist nicht 'weniger', sondern das Gegenteil")
    pruefe(P, "HALTEN braucht keine Richtung",
           validiere({**basis, "aktion": "HALTEN"}, "BTC", "hebel")["aktion"] == "HALTEN")
    try:
        validiere({**basis, "aktion": "ERÖFFNEN", "tranche_eur": 300}, "BTC", "spot")
        getrennt = False
    except EmpfehlungUngueltig:
        getrennt = True
    pruefe(P, "eine Hebel-Aktion ist bei Spot ungueltig", getrennt,
           "ohne das Instrument haette dieselbe Antwort je nach Aufrufer "
           "gegolten oder nicht")

    # DER PROMPT FRAGT DIE RICHTUNG, ABER NICHT DEN FAKTOR (Kapitel 11.6).
    p_hebel = rolle_trader.prompt_fuer("hebel", "einstieg")
    p_spot = rolle_trader.prompt_fuer("spot", "einstieg")
    pruefe(P, "der Hebel-Prompt nennt alle sieben Aktionen",
           all(a in p_hebel for a in AKTIONEN_HEBEL))
    pruefe(P, "er fragt nach LONG oder SHORT",
           "LONG" in p_hebel and "SHORT" in p_hebel)
    pruefe(P, "und verbietet ausdruecklich den Hebelfaktor",
           "KEINEN Hebelfaktor" in p_hebel,
           "der Faktor folgt aus Risikobudget und Liquidationsabstand - "
           "Kapitel 11.6: Risikoparameter kommen nicht vom Modell")
    pruefe(P, "der Spot-Prompt bleibt unveraendert bei fuenf",
           "NICHTS_TUN" in p_spot and "HEBEL_SENKEN" not in p_spot
           and "LONG" not in p_spot)

    # DAS SCHEMA HAENGT AM INSTRUMENT.
    sch_h = llm_schema.baue_trader_schema(rolle_trader, "hebel")
    sch_s = llm_schema.baue_trader_schema(rolle_trader, "spot")
    ph = sch_h.get("properties", sch_h)
    ps = sch_s.get("properties", sch_s)
    pruefe(P, "das Hebel-Schema erlaubt sieben Aktionen",
           len(ph["aktion"]["enum"]) == 7)
    pruefe(P, "und traegt das Richtungsfeld", "richtung" in ph
           and set(ph["richtung"]["enum"]) == set(RICHTUNGEN))
    pruefe(P, "das Spot-Schema traegt es NICHT", "richtung" not in ps,
           "ein Feld, das bei Spot nie gefuellt wird, waere eine Frage nach "
           "etwas, das es dort nicht gibt")

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
    pruefe(P, "das Hebel-Vokabular deckt sich mit der alten Kette",
           set(AKTIONEN_HEBEL) == set(REQUIRED_HEBEL_ACTIONS))
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
    pruefe(P, "die Stop-Untergrenzen stimmen mit der config ueberein",
           ER.GRENZEN["stop_min_relativ"] == 0.025
           and ER.GRENZEN["stop_min_atr"] == 0.75,
           "RM-1b/RM-1c - wer die config aendert, muss hier mitziehen")

    # --- EINHEITEN: eine Waehrung, eine Schreibweise? ---
    for datei in ("agent/signal_mail.py", "agent/faktenblock.py",
                  "agent/ausstiegsrechnung.py", "agent/entscheidungsrechnung.py"):
        pruefe(P, f"{datei.split('/')[-1]} schreibt Zahlen deutsch",
               "maketrans" in _quelltext(datei),
               "zwei Schreibweisen in einer Nachricht sind der Fehler aus "
               "Umbauplan 12.5")

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
    ohne_betrieb = []
    for m in module:
        rufer = [p for p, t in quellen.items()
                 if _re.search(rf"{m}", t) and not p.endswith(f"{m}.py")]
        if not any(p.startswith(("scheduler/", "ui/")) for p in rufer):
            ohne_betrieb.append(m)
    pruefe(P, "die fehlende Verdrahtung ist VOLLSTAENDIG, nicht teilweise",
           len(ohne_betrieb) == len(module),
           f"{len(ohne_betrieb)} von {len(module)} ohne Betriebsaufrufer. "
           f"Das ist der offene Punkt B1 und KEIN neuer Fund - aber solange "
           f"es ALLE sind, gibt es keine halb verdrahtete Kette, in der "
           f"unklar waere, welcher Weg gilt")


def paket_b1() -> None:
    """B1 - der eine Ort, an dem die Kette zusammengesetzt wird."""
    P = "B1"
    import sqlite3
    from agent import rollen_lauf as RL, rollen_eingabe as RE

    # DIE SCHUTZSCHALTER SIND WICHTIGER ALS DER DURCHLAUF.
    q = sqlite3.connect("data/tradinginfotool.db")
    con = sqlite3.connect(":memory:"); q.backup(con); q.close()
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
                "belege": [{"fakt": "Schwankung niedrig", "richtung": "dafuer",
                            "gewicht": "hoch"}],
                "unabhaengige_faktoren": 2,
                "begruendung": "Die Schwankung geht zurueck.",
                "was_dagegen": "Abstand zum Hoch.",
                "umgeworfen_durch": "Tagesschluss unter dem Jahrestief.",
                **({"einstieg_eur": round(k, 2),
                    "stop_eur": round(k - 2.5 * a, 2)} if kauft else {})}

    antworten = {"lagebild": {"lage": "Die Maerkte zeigen eine Divergenz.",
                              "klassen": [{"klasse": "krypto",
                                           "einstufung": "unguenstig",
                                           "warum": "Bitcoin steht tief."}],
                              "belege": ["Bitcoin steht tief."]},
                 "befund": {s: befund(s, s == "BTC") for s in symbole}}
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

    vorher = _inhalt("data/tradinginfotool.db")
    erg = RL.fuehre_lauf(conn=con, reihen=reihen, symbole=symbole,
                         betriebsart="trocken", antworten=antworten)
    pruefe(P, "der Trockenlauf laeuft ohne Fehler durch",
           not erg["fehler"], str(erg["fehler"][:2]))
    pruefe(P, "und schreibt KEINE Zeile in die Produktivdatenbank",
           _inhalt("data/tradinginfotool.db") == vorher,
           "die Verbindung wird uebergeben, nie hier geoeffnet - aber die "
           "Fakten-Module lesen mit ihrer eigenen Vorgabe, und das muss "
           "LESEN bleiben")
    pruefe(P, "er schreibt auch in die Kopie nichts",
           not erg["signale"],
           "trocken heisst: kein Modellaufruf, kein Schreiben, keine Mail")
    d = erg["durchlauf"]
    pruefe(P, "jedes Symbol hat alle Stufen durchlaufen",
           d.hinein == len(symbole) and d.bestanden_je_stufe["urteil"] == len(symbole))
    pruefe(P, "ein NICHTS_TUN faellt bei der Aktion heraus",
           d.verloren_je_stufe["aktion"] == len(symbole) - 1)
    pruefe(P, "fuer den Einstieg entsteht eine Mail", len(erg["mails"]) == 1)
    pruefe(P, "der Entscheider zaehlt, nimmt aber nichts heraus",
           d.heraus == 1 and d.verloren_je_stufe["entscheider"] >= 0)

    # EIN FEHLENDES SYMBOL WIRD GEZAEHLT, NICHT UEBERSPRUNGEN.
    erg2 = RL.fuehre_lauf(conn=con, reihen=reihen, symbole=symbole + ["GIBTSNICHT"],
                          betriebsart="trocken", antworten=antworten)
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
        if richtung:
            d["richtung"] = richtung
        if aktion in ("KAUFEN", "ERÖFFNEN"):
            d |= {"einstieg_eur": round(kk, 2), "stop_eur": round(kk - 2.5 * aa, 2)}
        return d

    def _lauf(inst, aktion, richtung=None, sym="ETH"):
        ant = {"lagebild": antworten["lagebild"],
               "befund": {sym: _antwort(sym, aktion, richtung)}}
        return RL.fuehre_lauf(conn=con, reihen=reihen, symbole=[sym],
                              betriebsart="trocken", instrument=inst,
                              strategie="einstieg", antworten=ant)

    pruefe(P, "ein Spot-Lauf erzeugt eine Mail",
           len(_lauf("spot", "KAUFEN")["mails"]) == 1)
    pruefe(P, "ein Hebel-Lauf ebenfalls",
           len(_lauf("hebel", "ERÖFFNEN", "LONG")["mails"]) == 1,
           "vorher war er gar nicht moeglich")
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
        aus = {}
        for zeile in text.split(chr(10)):
            z = zeile.strip()
            for name, wort in (("stop", "Stop "), ("ziel", "Take-Profit"),
                               ("liq", "Liquidation etwa")):
                if wort in z and name not in aus:
                    zahlen = [t for t in z.replace("(", " ").replace(")", " ").split()
                              if t.replace(".", "").replace(",", "").isdigit()]
                    if zahlen:
                        aus[name] = float(zahlen[0].replace(".", "").replace(",", "."))
        return aus

    kurs_eth = RE.kurs_eur("ETH", reihen["ETH"], len(reihen["ETH"]) - 1,
                           "data/tradinginfotool.db")
    lang = _marken(_lauf("hebel", "ERÖFFNEN", "LONG")["mails"][0]["text"])
    kurz = _marken(_lauf("hebel", "ERÖFFNEN", "SHORT")["mails"][0]["text"])
    pruefe(P, "bei LONG liegt der Stop unter dem Kurs, bei SHORT darueber",
           lang["stop"] < kurs_eth < kurz["stop"],
           f"LONG {lang.get('stop')} / SHORT {kurz.get('stop')} bei {kurs_eth:.0f}")
    pruefe(P, "das Ziel dreht mit",
           lang["ziel"] > kurs_eth > kurz["ziel"])
    pruefe(P, "und die Liquidation auch",
           lang["liq"] < kurs_eth < kurz["liq"],
           "sonst stuende bei einem SHORT eine Liquidation unter dem "
           "Einstieg - dort kann sie nie greifen")
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
    pruefe(P, "die vierzehn Spalten der Rollen-Kette sind namentlich drin",
           all(sp in EX._SPOT_SIGNAL_SPALTEN for sp in
               ("quelle_kette", "lagebild_id", "prompt_stand", "fx_eur_je_usd",
                "unabhaengige_faktoren", "umgeworfen_durch",
                "umgeworfen_preis_eur", "umgeworfen_bis",
                "schwankung_perzentil", "momentum_perzentil",
                "volumen_perzentil", "zai_stimmen", "richtung", "hebel")),
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
               "umgeworfen_preis_eur": 90.0, "umgeworfen_bis": "2026-09-01",
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
    pruefe(P, "das geschriebene Signal erscheint in der Trefferbilanz",
           sum(e["faelle"] for e in bilanz.values()) >= 1,
           "vor dem 13.08. lieferte zaehle() dauerhaft {} - der Entscheider "
           "rechnete nicht mit wenig Daten, sondern mit null")
    schluessel = next(iter(bilanz), None)
    if schluessel is None:
        pruefe(P, "ohne Bilanz sind die folgenden Pruefungen nicht pruefbar",
               False, "abgebrochen statt gruen gemeldet")
        c.close(); return
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
    pruefe(P, "faellt die Konsistenzpruefung aus, laeuft der Richtungsabgleich",
           aus2.get("eigene_richtung") == "SHORT" and "urteil" not in aus2,
           f"bekommen: {aus2} - ein gemeinsamer try-Block haette beide verloren")
    pruefe(P, "und der Widerspruch wird als solcher gebucht",
           aus2.get("uebereinstimmung") == "nein",
           "KAUFEN gegen SHORT ist eine Abweichung, keine Uebereinstimmung")

    # KEIN VERGLEICH OHNE VERGLEICHSBASIS.
    aus3 = ZM.hole(faktentext={"a": 1}, urteil={"aktion": "NICHTS_TUN"},
                   zai_client=_HalbKaputt(), warte_max_s=20)
    pruefe(P, "bei NICHTS_TUN wird KEINE Uebereinstimmung behauptet",
           "uebereinstimmung" not in aus3,
           "richtung_aus_action() liefert dort bewusst None - ein 'nein' waere "
           "eine Abweichung von einer Richtung, die niemand behauptet hat")

    pruefe(P, "ohne Ergebnis entsteht KEINE leere Mailzeile", ZM.zeilen({}) == [],
           "ein Abschnitt 'Zweite Meinung: -' saehe aus wie ein Befund und "
           "waere ein Ausfall - der Leser kann beides nicht unterscheiden")
    zeilen = ZM.zeilen(aus2)
    pruefe(P, "der Widerspruch steht in der Mail und wird benannt",
           any("WIDERSPRICHT" in z for z in zeilen), f"{zeilen}")

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
            if self.aufrufe == 1:
                return _j.dumps(_lagebild, ensure_ascii=False)
            sym = next((s for s in symbole if s in inhalt), symbole[0])
            return _j.dumps(_befund(sym, sym == "BTC"), ensure_ascii=False)

    klient = _Aufzeichnung()
    vor = c.execute("SELECT COUNT(*) FROM signals "
                    "WHERE quelle_kette='rollen'").fetchone()[0]
    erg = RL.fuehre_lauf(conn=c, reihen=reihen, symbole=symbole,
                         betriebsart="probe", client=klient, modell="test",
                         zai_client=None)
    pruefe(P, "der Probelauf laeuft ohne Fehler durch",
           not erg["fehler"], str(erg["fehler"][:2]))
    nach = c.execute("SELECT COUNT(*) FROM signals "
                     "WHERE quelle_kette='rollen'").fetchone()[0]
    pruefe(P, "und schreibt eine Signalzeile - erstmals ueberhaupt",
           nach > vor, f"{vor} -> {nach}")
    pruefe(P, "die Mail traegt die Kennung des geschriebenen Signals",
           any(m.get("signal_id") for m in erg["mails"]),
           "ohne sie liesse sich eine verschickte Mail spaeter keinem "
           "Datensatz zuordnen")
    neu = c.execute(
        "SELECT schwankung_perzentil, momentum_perzentil, volumen_perzentil, "
        "lagebild_id FROM signals WHERE quelle_kette='rollen' "
        "ORDER BY id DESC LIMIT 1").fetchone()
    pruefe(P, "die drei Familien und das Lagebild stehen an der Zeile",
           all(w is not None for w in neu), f"gespeichert: {neu}")
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
    pruefe(P, "die Kette uebergibt ihre EIGENEN Prompts",
           "system_prompt = SYSTEM_KONSISTENZ" in zm_code
           and "system_prompt = SYSTEM_RICHTUNG" in zm_code,
           "ohne die Uebergabe griffen still die alten")
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
    pruefe(P, "ein Kleinwert behaelt seine Stellen",
           _kurs(0.00034567) == "0.000346",
           "die Genauigkeit haengt an der Groessenordnung, nicht an einer "
           "Konstante - sonst waere die Marke fuer ein Token unbrauchbar")
    import json as _json
    import re as _re
    _, _bc = RE.baue_fall(symbol=symbole[0], reihe=reihen[symbole[0]],
                          index=len(reihen[symbole[0]]) - 1, reihen=reihen,
                          db="data/tradinginfotool.db", mit_finanzierung=False)
    _text = _json.dumps(_bc, ensure_ascii=False)
    _uebergenau = _re.findall(r"\d{4,}\.\d{3,}", _text)
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
    pruefe(P, "Z.ai prueft Text gegen FAKTEN - und bekommt die Aktion nicht",
           "pruefe_konsistenz" in zm_code and "aktion" not in
           zm_code.split("pruefe_konsistenz")[1].split(")")[0],
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
    pruefe(P, "gezaehlt wird EINMAL je Lauf, nicht je Asset",
           _lauf.find("TB . zaehle ( conn") < _lauf.find("for symbol in symbole"),
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

    _einig = ZM.mehrheit(_Fest(["SHORT"]), {"asset": "X", "stand": ["a", "b"]})
    pruefe(P, "drei gleiche Stimmen ergeben 3 von 3",
           _einig["stimmen"] == 3 and _einig["von"] == 3
           and _einig["eigene_richtung"] == "SHORT", str(_einig))
    _knapp = ZM.mehrheit(_Fest(["SHORT", "NEUTRAL", "SHORT"]),
                         {"asset": "X", "stand": ["a", "b"]})
    pruefe(P, "zwei von drei gewinnen, und die Knappheit bleibt sichtbar",
           _knapp["eigene_richtung"] == "SHORT" and _knapp["stimmen"] == 2,
           f"{_knapp} - ein 2:1 darf nicht aussehen wie ein 3:0")
    pruefe(P, "und die Mail sagt es auch",
           "2 von 3, uneinheitlich" in ZM.zeilen(_knapp)[0],
           ZM.zeilen(_knapp)[0])
    pruefe(P, "bei Einigkeit steht kein Warnwort da",
           "uneinheitlich" not in ZM.zeilen(_einig)[0], ZM.zeilen(_einig)[0])
    pruefe(P, "faellt jede Stimme aus, gibt es kein Urteil",
           ZM.mehrheit(_Fest([None]), {"asset": "X", "stand": ["a"]}) is None,
           "eine erfundene Richtung waere schlimmer als keine")
    pruefe(P, "eine ausgefallene Stimme kippt den Rest nicht",
           (ZM.mehrheit(_Fest([None, "LONG", "LONG"]),
                        {"asset": "X", "stand": ["a"]}) or {}).get("von") == 2,
           "gezaehlt wird, was zurueckkam - nicht, was gefragt wurde")

    _zm2 = _nur_code("agent/zweite_meinung.py")
    pruefe(P, "die mittlere Stimme laeuft auf umgekehrter Satzreihenfolge",
           "kehre_saetze_um ( fakten ) if i == 1 else fakten" in _zm2,
           "so steckt der alte Positionstest weiter drin, ohne einen eigenen "
           "Aufruf zu kosten")
    pruefe(P, "die Kette ruft NICHT mehr die Zweierfassung",
           "leite_eigene_richtung_positionsrobust" not in _zm2,
           "sie faellt bei Uneinigkeit auf NEUTRAL zurueck und verwischt "
           "genau das, was jetzt sichtbar sein soll")
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
    _mit = SA.felder_aus_entscheidung(
        {"aktion": "ERÖFFNEN", "richtung": "SHORT", "begruendung": "x"},
        fakten={}, rechnung={"hebel": 4.5})
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

    # L1 DIE CRV-ABSTUFUNG - die einzige GEMESSENE Groessenregel der alten Kette.
    pruefe(P, "bei CRV 2,0 nur ein Fuenftel der vollen Groesse",
           abs(ER._crv_faktor(2.0, "spot") - 0.2) < 1e-9,
           f"Spreizung {ER.GRENZEN['crv_spreizung']} -> Sockel 1/5")
    pruefe(P, "ab CRV 6,0 die volle Groesse",
           ER._crv_faktor(6.0, "spot") == 1.0
           and ER._crv_faktor(9.0, "spot") == 1.0,
           "oberhalb wird nicht weiter belohnt")
    pruefe(P, "dazwischen stufenlos, nicht in Spruengen",
           ER._crv_faktor(2.0, "spot") < ER._crv_faktor(3.0, "spot")
           < ER._crv_faktor(4.5, "spot") < ER._crv_faktor(6.0, "spot"),
           "vorher bekamen CRV 2,5 und CRV 6,0 dieselbe Groesse")
    pruefe(P, "der Faktor kann NIE vergroessern",
           all(ER._crv_faktor(c / 10, "spot") <= 1.0 for c in range(0, 200)),
           "sicher durch Bauform - eine Ueberexposition ist ausgeschlossen, "
           "nicht bloss unwahrscheinlich")
    # DIE WICHTIGSTE DIESER PRUEFUNGEN.
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
    pruefe(P, "und der Grund nennt den CRV",
           "CRV-Abstufung" in str(_r.get("betrag_gedeckelt_durch") or ""),
           f"Faktor {_r['crv_groessenfaktor']}, "
           f"Grund {_r.get('betrag_gedeckelt_durch')}")

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
    _mit = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=150.0, instrument="spot",
                     umgeworfen_preis_eur=94.0, cash_frei_eur=300.0)
    _ohne = ER.rechne(kurs=100.0, atr=3.0, risiko_eur=150.0, instrument="spot",
                      umgeworfen_preis_eur=94.0)
    pruefe(P, "knappes Cash macht die Position kleiner",
           _mit["betrag_eur"] < _ohne["betrag_eur"], 
           f"{_mit['betrag_eur']} gegen {_ohne['betrag_eur']} EUR")
    pruefe(P, "und sagt das auch mit eigenem Grund",
           "Cash" in str(_mit.get("betrag_gedeckelt_durch") or ""),
           "waeren Topf und Cash EIN Wert, sagte die Notiz 'Topf', wo in "
           "Wahrheit das Geld fehlt")
    pruefe(P, "ohne ermittelbares Cash gibt es KEINE Sperre",
           ER.rechne(kurs=100.0, atr=3.0, risiko_eur=150.0, instrument="spot",
                     umgeworfen_preis_eur=94.0,
                     cash_frei_eur=None)["betrag_eur"] > 0,
           "eine Reserve, die wegen einer fehlenden Zahl ALLES sperrt, waere "
           "schlimmer als keine")
    pruefe(P, "der Trockenlauf fragt das Cash gar nicht ab",
           "if betriebsart != TROCKEN else None" in _nur_code(
               "agent/rollen_lauf.py"),
           "er hat keine Verbindung zu einer echten Lage")

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


PAKETE = {"0": paket_0, "1": lambda: (paket_1(), paket_1_schema()),
          "2": paket_2, "3": paket_3, "4": paket_4, "5": paket_5,
          "6": paket_6, "7": paket_7, "8": paket_8, "9": paket_9,
          "10": paket_10, "11": paket_11, "12": paket_12, "13": paket_13, "14": paket_14, "12c": paket_12c, "12b": paket_12b, "12d": paket_12d, "13": paket_13, "gesamt": gesamtpruefung, "B1": paket_b1, "Export": paket_export, "15": paket_15}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paket", default=None, help="nur dieses Paket pruefen")
    a = ap.parse_args()
    laufen = [a.paket] if a.paket else sorted(PAKETE)
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


if __name__ == "__main__":
    raise SystemExit(main())
