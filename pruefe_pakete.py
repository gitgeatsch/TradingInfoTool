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
    pruefe(P, "und sie fragt gar nicht, wenn keine Positionierung vorliegt",
           'len(lage.get("fehlt") or []) >= 3' in _quelltext(
               "agent/zweite_meinung.py"),
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
    _e_btc, _ = AS.darf_analysiert_werden(
        None, "BTC", "hebel", "einstieg", watchlist=_wl_test)
    pruefe(P, "und ein normales Asset bleibt unberuehrt", _e_btc is True)
    # DIE VERDRAHTUNG - `_ein_asset` sieht `_wl` NICHT von selbst. Genau diese
    # Falle hat am 14.08. `VK` erwischt: eine Variable aus `fuehre_lauf`, der
    # breite Fehlerfang schluckt den NameError, und JEDES Symbol landet im
    # Fehlerzweig.
    import inspect as _i5
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
    pruefe(P, "und die Geradeziehung laeuft VOR dem ersten Kettenlauf",
           "_migrate_hebel_schalter_geradeziehen ( conn )" in _nur_code(
               "database/db.py").split("def init_db")[1][:2000],
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
    pruefe(P, "nur Krypto laeuft mit zwei Instrumenten",
           [g for g, i, _ in AK.laeufe() if i == "hebel"] == ["krypto"],
           "Hebel gibt es bei Bitpanda nur dort")
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
    pruefe(P, "der Umlauf faehrt sechs Kombinationen",
           len(AK3.laeufe()) == 6, str([(g, i) for g, i, _ in AK3.laeufe()]))
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
    pruefe(P, "ein Spot-Urteil sperrt den Hebel NICHT",
           WH4.gesperrt_bis(_c4, "BTC", "spot", jetzt=_jetzt) is not None
           and WH4.gesperrt_bis(_c4, "BTC", "hebel", jetzt=_jetzt) is None,
           "'soll ich BTC mit Hebel handeln' ist eine andere Frage als 'soll "
           "ich eine Spot-Tranche nachlegen' - andere Geometrie, andere "
           "Kosten, andere Haltedauer")
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
    _spot = LB3.geteilt(symbol="TST", reihe=_reihe, index=89, kurs_eur=144.5,
                        atr=1.2, menge=3.0, einstand_eur=100.0,
                        finanzierung=_fin, instrument="spot")
    _heb = LB3.geteilt(symbol="TST", reihe=_reihe, index=89, kurs_eur=144.5,
                       atr=1.2, menge=3.0, einstand_eur=100.0,
                       finanzierung=_fin, instrument="hebel")

    # SCHRITT 2 - die Finanzierung verlaesst den Spot-Prompt.
    pruefe(P, "Finanzierung steht NUR noch im Hebel-Faktensatz",
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

    pruefe(P, "der Liquidationsabstand steht NUR im Hebel-Faktensatz",
           not _spot["hebelgeometrie"] and len(_heb["hebelgeometrie"]) == 2,
           "ein Spot-Kauf kann nicht zwangsaufgeloest werden - der Satz waere "
           "dort schlicht falsch")
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
    pruefe(P, "und der echte Ausfall wuerde jetzt erkannt",
           ST5.is_history_stale("2026-08-14", schwelle_tage=1)
           is not ST5.is_history_stale("2026-08-14"),
           "Freitag-Kerze am Sonntag: alte Schwelle schweigt, neue schlaegt an")
    pruefe(P, "die geteilte Schwelle bleibt unangetastet",
           "HISTORY_STALE_THRESHOLD_DAYS = 2" in _quelltext("staleness.py"),
           "an ihr haengen die Anzeige und das Gate R-5.0 der alten Kette - "
           "sie zu senken waere die Verschlimmbesserung")
    pruefe(P, "der Kraken-Check benutzt die engere",
           "schwelle_tage=staleness.KRYPTO_OHLC_STALE_THRESHOLD_DAYS"
           in _quelltext("scheduler/background.py"),
           "sonst greift der Sofortlauf beim Neustart weiterhin nicht")

    from agent import rolle_trader as RT5

    pruefe(P, "der Prompt-Stand ist mitgezogen",
           RT5.PROMPT_STAND == "2026-08-16b",
           "jeder Messbefund gehoert zu einem Stand - ohne den Sprung waeren "
           "Messungen vor und nach Phase I nicht unterscheidbar")

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
    pruefe(P, "beim Hebel kostet die HALTEDAUER, nicht nur der Trade",
           _hebel_lang > _hebel_kurz * 2,
           f"2 Tage {_hebel_kurz:.3f} R gegen 30 Tage {_hebel_lang:.3f} R - "
           "die Tagesstaffel auf geliehenes Kapital fehlte der neuen Kette "
           "vollstaendig; sie rechnete pauschal mit dem Krypto-Satz")
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
        pruefe(P, "und der Cooldown trennt sie ebenfalls",
               WH6.gesperrt_bis(_c6, "DBPK", "absicherung", jetzt=_j) is not None
               and WH6.gesperrt_bis(_c6, "DBPK", "spot", jetzt=_j) is None,
               "dieselbe Funktion, also automatisch dieselbe Trennung - das "
               "ist der Gewinn daraus, dass es sie nur einmal gibt")

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
    pruefe(P, "gezaehlt wird NUR, wo ein Aufruf stattfand",
           'if ergebnis["aufrufe"] > _vor_aufrufe:' in _q9,
           "ein gesperrtes Symbol kostet nichts und darf die Wache nicht "
           "ausloesen - sonst hielte ausgerechnet der sparsame Fall den Lauf an")
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
           'getattr(pos, "positionsmenge", None)' in _q9,
           "`quantity` gibt es dort nicht - die Abfrage haette still 0 "
           "geliefert und jedes SCHLIESSEN zum Schatten gemacht")
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
    pruefe(P, "keine Hebel-Aktion faellt mehr durch alle Raster",
           _ohne == ["HALTEN"],
           f"ohne Klasse: {_ohne} - nur HALTEN darf uebrigbleiben, denn es "
           "aendert nichts")
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
    pruefe(P, "eine GRUPPE ist spezifischer als ein INSTRUMENT",
           WH13.stunden("spot", _cfg13, "aktien") == 24.0
           and WH13.stunden("spot", _cfg13, "krypto") == 15.0,
           f"aktien {WH13.stunden('spot', _cfg13, 'aktien')} h - eine Aktie "
           "handelt nicht rund um die Uhr; ein 15-Stunden-Takt fragt dort "
           "mehrfach am selben Handelstag dasselbe")
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
