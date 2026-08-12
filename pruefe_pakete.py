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
    pruefe(P, "fehlende Angaben bekommen ein EIGENES Band",
           TB.merkmale(unabhaengige_faktoren=None)[0] is None
           and TB.merkmale(unabhaengige_faktoren=0)[0] == 0,
           "sie stillschweigend einzusortieren hiesse, Faelle zu zaehlen, die "
           "dort nicht hingehoeren")
    pruefe(P, "die Baender sind grob genug",
           len({TB.merkmale(unabhaengige_faktoren=n)[0] for n in range(0, 9)}) == 4,
           "eine Tabelle mit tausend Zellen hat in jeder drei Faelle")

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


PAKETE = {"0": paket_0, "1": lambda: (paket_1(), paket_1_schema()),
          "2": paket_2, "3": paket_3, "4": paket_4, "5": paket_5,
          "6": paket_6, "7": paket_7, "8": paket_8, "9": paket_9,
          "10": paket_10}


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
