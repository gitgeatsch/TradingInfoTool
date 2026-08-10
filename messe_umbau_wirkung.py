"""Wirkt der Umbau? Alt gegen neu, je Fakt, gepaart (2026-08-09).

WAS UMGEBAUT WURDE, und warum es gemessen werden muss BEVOR es live geht:

    Trefferquote   vorher die nackte absolute Quote (16,0 %), jetzt mit
                   CRV-Breakeven als Bezug, je Richtung getrennt und zum
                   jeweiligen Breakeven hin geschrumpft.
    Systemguete    vorher der nackte Erwartungswert (-0,149 R), jetzt mit
                   Basislinie (-0,094 R), Signalbeitrag (-0,055 R) und
                   Vertrauensbereich ([-0,407; +0,147], enthaelt die NULL).

BEIDE WAREN GEMESSEN SCHAEDLICH (09.08., Gemini, 36 Anker, gepaart): sie
druecken die LONG-Konfidenz um 4,9 bis 33,3 Punkte und die SHORT-Konfidenz um
NULL - eine gerichtete Wirkung, obwohl LONG mit 16,2 % Trefferquote sogar
leicht BESSER liegt als SHORT mit 15,0 %.

DIE FUENF ARME, alle auf denselben Ankern:

    A1        Grundlinie, ohne beide Fakten
    Q_alt     Trefferquote wie HEUTE
    Q_neu     Trefferquote UMGEBAUT
    G_alt     Systemguete wie HEUTE
    G_neu     Systemguete UMGEBAUT

DIE NEUEN FORMEN KOMMEN AUS DEN ECHTEN PRODUKTIVFUNKTIONEN, nicht aus einem
Nachbau: `compute_win_rate_fact()` und `systemguete_kontext_fuer_prompt()`
liefern sie gegen die Produktionskopie. Die ALTEN Formen entstehen daraus
durch Entfernen der neuen Felder. Damit ist zugesichert, dass "neu" exakt das
ist, was ausgeliefert wuerde - und dass sich alt und neu in NICHTS ausser
diesen Feldern unterscheiden, insbesondere nicht in den Rohzahlen.

RAUSCHBODEN: uebernommen mit 0,83 Konfidenzpunkten aus dem Kettennaht-Lauf
desselben Tages, desselben Anbieters und derselben Ankermenge. Ein sechster
Arm nur dafuer waere Kontingent ohne Erkenntnisgewinn.

ENTSCHEIDUNGSREGEL, VOR dem Lauf festgelegt:

    Der Umbau gilt als wirksam, wenn Q_neu und G_neu die LONG-Konfidenz
    WENIGER druecken als ihre Alt-Varianten, und zwar ueber dem Rauschboden.

    GEGENKONTROLLE, ohne die es nicht zaehlt: die SHORT-Seite darf sich dabei
    NICHT in die Gegenrichtung bewegen. Ein Umbau, der nur LONG anhebt und
    SHORT absenkt, haette die Asymmetrie gedreht statt aufgeloest - und waere
    damit derselbe Fehler mit umgekehrtem Vorzeichen.

    python messe_umbau_wirkung.py --anker 30 --trocken
    python messe_umbau_wirkung.py --anker 30 --ausgabe umbau.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import statistics
import sys
import time
from collections import Counter

from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
from messe_kettennaht_eingriffe import _gepaart, _vergleich
from pruefe_auswertbarkeit import pruefe_auswertbarkeit
import messe_regimephasen_llm as M

ARME = ("A1", "Q_alt", "Q_neu", "G_alt", "G_neu")


def verschraenke_phasen(je_phase: dict, phasen, label: dict, reihen: dict,
                        hoechstens: int) -> list:
    """Anker REIHUM ueber die Phasen einsammeln, nicht Phase fuer Phase.

    DER FALL (09.08. abends, echter Lauf). Die vorherige Fassung haengte die
    Phasen aneinander und sortierte alles nach DATUM. Die Baerenphase ist die
    juengste - ihre Anker standen damit am ENDE der Liste. Als der Lauf nach
    25 von 60 Ankern abbrach, enthielt die Stichprobe:

        BULLE 17, SEITWAERTS 8, BAER 0

    Ausgerechnet die Phase, in der die Produktion tatsaechlich laeuft, fehlte
    vollstaendig. Und weil der Grundlinienarm in Bullen- und Seitwaertsphasen
    durchgehend LONG waehlt (25 von 25), gab es keine einzige gepaarte
    SHORT-Zelle - die Kontrollbedingung der Messregel war nicht pruefbar.
    Beide Defekte hatten dieselbe Wurzel.

    Reihum heisst: erst bekommt jede Phase einen Anker, dann jede einen
    zweiten, und so fort. Damit ist JEDER ANFANG der Liste phasenausgewogen,
    und ein frueher Abbruch verzerrt die Mischung nicht mehr.

    Das ist dieselbe Lehre wie beim Stichproben-Alias, den die Gegenkontrolle
    D1g in messe_regimephasen_llm.waehle_anker() gefunden hat - eine
    Sortierung, die unter Kuerzung systematisch etwas abschneidet. Dort waren
    es Symbole, hier Phasen: eine Ebene hoeher, gleicher Fehler.

    Innerhalb einer Phase bleibt die Datumssortierung - sie macht den Lauf
    nachvollziehbar und schneidet nichts ab, weil reihum gezogen wird."""
    je_phase_sortiert = {}
    for phase in phasen:
        eintraege = [(phase, label[phase], sym, i)
                     for sym, i in je_phase.get(phase, [])]
        eintraege.sort(key=lambda x: (reihen[x[2]][x[3]].date, x[2]))
        je_phase_sortiert[phase] = eintraege

    anker: list = []
    runde = 0
    while len(anker) < hoechstens:
        vorher = len(anker)
        for phase in phasen:
            eintraege = je_phase_sortiert[phase]
            if runde < len(eintraege) and len(anker) < hoechstens:
                anker.append(eintraege[runde])
        if len(anker) == vorher:      # keine Phase hat mehr Nachschub
            break
        runde += 1
    return anker

# JE ANBIETER SEIN EIGENER RAUSCHBODEN - gemessen am 09.08. mit
# `pruefe_llm_stabilitaet.py`, 12 Anker x 3 Wiederholungen bei bitgleicher
# Eingabe. Den Gemini-Wert auf einen OpenRouter-Lauf anzuwenden waere ein
# Massstab aus dem falschen Versuch: nemotron streut mehr als dreimal so
# stark, und ein Effekt, der bei Gemini ueber dem Boden liegt, kann bei
# OpenRouter darunter liegen.
RAUSCHBODEN = {"gemini": 0.83, "openrouter": 2.20}

# Welche Felder die NEUE Form der Trefferquote ausmachen - genau diese werden
# fuer die Alt-Variante entfernt. Die Rohzahlen bleiben in beiden identisch.
# NACHGEZOGEN nach dem Struktur-Umbau vom 09.08.: `geschrumpft` wurde flach
# aufgeloest, deshalb heissen die Felder jetzt anders. Die Eingriffskontrolle
# hat den Lauf korrekt abgebrochen, als die Liste veraltet war - genau dafuer
# ist sie da.
NEU_QUOTE = ("crv_median", "breakeven_trefferquote_pct",
             "vorsprung_vor_breakeven_pp", "trefferquote_gewichtet",
             "gewicht", "einordnung", "belastbar", "je_richtung",
             "nicht_enthalten_ueberholt")
NEU_GUETE = ("basislinie_erwartungswert_r", "signalbeitrag_r",
             "basislinie_anzahl", "erwartungswert_ci", "aufloesungsquote",
             "erwartungswert_gewichtet", "signalbeitrag_gewichtet",
             "gewicht", "einordnung", "ci_enthaelt_null", "belastbar",
             "vorlaeufig_hinweis")

# Der alte Hinweis-Text, wortgleich aus der Fassung vor dem Umbau. Ihn
# nachzubauen statt zu zitieren waere ein anderer Reiz und damit ein anderer
# Versuch.
ALT_HINWEIS = "Basiert auf {n} bisher ausgewerteten Signalen."
ALT_LESEHILFE = (
    "Erwartungswert in R = durchschnittliches Ergebnis je Signal, gemessen "
    "an tatsaechlich eroeffneten Trades dieser Kategorie. Ein negativer Wert "
    "heisst, dass die bisherigen Signale im Schnitt Geld gekostet haben."
)


def hole_echte_fakten(db: str) -> tuple[dict, dict]:
    """Die NEUEN Formen aus den echten Produktivfunktionen."""
    from agent.krypto.backward_tracking import (
        compute_win_rate_fact, systemguete_kontext_fuer_prompt)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return (compute_win_rate_fact(conn, "hebel"),
            systemguete_kontext_fuer_prompt(conn))


def als_alt(neu: dict, felder: tuple, hinweis_schluessel: str,
            hinweis_alt: str) -> dict:
    """Die alte Form: neue Felder raus, alter Hinweistext rein."""
    alt = {k: v for k, v in neu.items() if k not in felder}
    alt[hinweis_schluessel] = hinweis_alt
    return alt


def baue_arm(fakten: dict, arm: str, label: str, quote_neu: dict,
             quote_alt: dict, guete_neu: dict, guete_alt: dict) -> dict:
    neu = json.loads(json.dumps(fakten))
    neu["regime"] = dict(neu.get("regime") or {})
    neu["regime"]["wert"] = label
    neu["regime"]["quelle"] = "historische EMA-Ordnung des BTC am Ankertag"
    if arm in ("Q_alt", "Q_neu"):
        neu["historische_erfolgsquote"] = dict(
            quote_alt if arm == "Q_alt" else quote_neu)
        # Nur wenn die Quote wirklich mitgeliefert wird, darf der
        # Verfuegbarkeitsvermerk weg - in BEIDEN Varianten gleich.
        neu["nicht_verfuegbar"] = [x for x in (neu.get("nicht_verfuegbar") or [])
                                   if x != "historische_erfolgsquote"]
    if arm in ("G_alt", "G_neu"):
        neu["systemguete"] = dict(guete_alt if arm == "G_alt" else guete_neu)
    return neu


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=30)
    p.add_argument("--je-symbol", type=int, default=5)
    p.add_argument("--pause", type=float, default=0.2)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--anbieter", choices=("gemini", "openrouter"),
                   default="gemini")
    # 2026-08-09: Geminis Kontingent ist PRO MODELL (500/Tag). Ein erschoepftes
    # Modell heisst nicht erschoepfter Zugang - das Geschwistermodell hat einen
    # eigenen Topf. Ohne diese Option musste ein Messlauf warten, bis unser
    # Produktionsmodell wieder frei war, und nahm ihm dann das Budget weg.
    p.add_argument("--modell", default=None,
                   help="Gemini-Modell; ohne Angabe das Vorgabemodell")
    p.add_argument("--db", default="C:/Users/Geatsch/AppData/Local/Temp/claude/"
                   "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
                   "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")
    p.add_argument("--richtungen-noetig", action="store_true", default=True,
                   help="die Fragestellung braucht LONG- UND SHORT-Zellen")
    p.add_argument("--trotzdem-weiter", action="store_true",
                   help="nicht abbrechen, wenn die Auswertbarkeit fehlt - nur bewusst benutzen")
    p.add_argument("--ausgabe", default="umbau.json")
    args = p.parse_args()

    quote_neu, guete_neu = hole_echte_fakten(args.db)
    if not quote_neu or not guete_neu:
        print("Fakten nicht baubar - Abbruch.")
        return 1
    quote_alt = als_alt(quote_neu, NEU_QUOTE, "hinweis",
                        ALT_HINWEIS.format(n=quote_neu["anzahl_ausgewertete_signale"]))
    guete_alt = als_alt(guete_neu, NEU_GUETE, "lesehilfe", ALT_LESEHILFE)

    reihen = lade_reihen()
    btc = reihen["BTC"]
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.anker, args.je_symbol)
    anker = verschraenke_phasen(je_phase, M.ARME, M.LABEL, reihen, args.anker)

    print(f"Anker {len(anker)}, {len({a[2] for a in anker})} Symbole, "
          f"Phasen {dict(Counter(a[0] for a in anker))}")
    print(f"{len(ARME)} Arme -> {len(anker) * len(ARME)} Aufrufe")
    boden = RAUSCHBODEN[args.anbieter]
    print(f"Anbieter {args.anbieter}, Rauschboden {boden:.2f} Punkte "
          f"(gemessen 09.08. an diesem Anbieter)")

    print("\n=== EINGRIFFSKONTROLLE ===")
    probe = baue_historische_fakten(anker[0][2], reihen[anker[0][2]],
                                    anker[0][3], btc)
    pruefungen = []
    b = {a: baue_arm(probe, a, anker[0][1], quote_neu, quote_alt,
                     guete_neu, guete_alt) for a in ARME}
    pruefungen.append(("A1 traegt WEDER Trefferquote NOCH Systemguete",
                       "historische_erfolgsquote" not in b["A1"]
                       and "systemguete" not in b["A1"], ""))
    pruefungen.append(("Q_alt ohne die neuen Felder",
                       all(f not in b["Q_alt"]["historische_erfolgsquote"]
                           for f in NEU_QUOTE), ""))
    pruefungen.append(("Q_neu MIT allen neuen Feldern",
                       all(f in b["Q_neu"]["historische_erfolgsquote"]
                           for f in NEU_QUOTE), ""))
    pruefungen.append((
        "Q_alt und Q_neu tragen DIESELBE Rohzahl (sonst zwei Versuche)",
        b["Q_alt"]["historische_erfolgsquote"]["trefferquote_pct"]
        == b["Q_neu"]["historische_erfolgsquote"]["trefferquote_pct"],
        str(b["Q_neu"]["historische_erfolgsquote"]["trefferquote_pct"])))
    pruefungen.append(("G_alt ohne die neuen Felder",
                       all(f not in b["G_alt"]["systemguete"] for f in NEU_GUETE), ""))
    pruefungen.append(("G_neu MIT allen neuen Feldern",
                       all(f in b["G_neu"]["systemguete"] for f in NEU_GUETE), ""))
    pruefungen.append((
        "G_alt und G_neu tragen DENSELBEN Erwartungswert",
        b["G_alt"]["systemguete"]["erwartungswert_r"]
        == b["G_neu"]["systemguete"]["erwartungswert_r"],
        str(b["G_neu"]["systemguete"]["erwartungswert_r"])))
    pruefungen.append((
        "der Verfuegbarkeitsvermerk passt in BEIDEN Quote-Armen",
        all("historische_erfolgsquote" not in (b[a].get("nicht_verfuegbar") or [])
            for a in ("Q_alt", "Q_neu"))
        and "historische_erfolgsquote" in (b["A1"].get("nicht_verfuegbar") or []),
        ""))
    pruefungen.append(("Q-Arme tragen KEINE Systemguete (sonst zwei Aenderungen)",
                       all("systemguete" not in b[a] for a in ("Q_alt", "Q_neu")), ""))
    pruefungen.append(("G-Arme tragen KEINE Trefferquote",
                       all("historische_erfolgsquote" not in b[a]
                           for a in ("G_alt", "G_neu")), ""))
    alles = True
    for name, ok, detail in pruefungen:
        print(f"  {'[ok]    ' if ok else '[FEHLER]'} {name}"
              + (f"   {detail}" if detail else ""))
        alles &= ok
    if not alles:
        print("\n  ABBRUCH: die Arme unterscheiden sich nicht wie beabsichtigt.")
        return 2

    print(f"\n  Trefferquote roh {quote_neu['trefferquote_pct']} %, "
          f"neu zusaetzlich: Breakeven {quote_neu['breakeven_trefferquote_pct']} %, "
          f"Abstand {quote_neu['vorsprung_vor_breakeven_pp']:+.1f} pp")
    print(f"  Systemguete roh {guete_neu['erwartungswert_r']} R, "
          f"neu zusaetzlich: Basislinie {guete_neu['basislinie_erwartungswert_r']} R, "
          f"Beitrag {guete_neu['signalbeitrag_r']} R, "
          f"CI {guete_neu['erwartungswert_ci']}")

    if args.trocken:
        zaehler = [0]

        def frage(fakten, sym):
            zaehler[0] += 1
            n = zaehler[0]
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            streu = ((n * 2654435761) >> 16) % 100 / 100.0
            q = fakten.get("historische_erfolgsquote") or {}
            g = fakten.get("systemguete") or {}
            # Der Mock bildet die ERWARTETE Wirkung nach: der nackte Fakt
            # daempft LONG stark, die umgebaute Fassung schwaecher, SHORT
            # bleibt unberuehrt. So wird die Auswertung an einem Fall mit
            # bekannter Antwort geprueft statt an einer Attrappe.
            # GEGEN VERALTEN GEBAUT (2026-08-10). Hier stand `"geschrumpft" in
            # q` - ein Feldname, den der Struktur-Umbau vom 09.08. flach
            # aufgeloest hat. Seither war die Bedingung IMMER falsch: Q_alt und
            # Q_neu bekamen dieselbe Strafe, der Trockenlauf simulierte gar
            # keinen Unterschied mehr und konnte die Auswertung nicht laenger
            # an einem Fall mit bekannter Antwort pruefen. Ein stiller Ausfall
            # der Selbstkontrolle, genau wie die veraltete Feldliste, die die
            # Eingriffskontrolle schon einmal abgefangen hat.
            #
            # Jetzt gegen die Feldlisten selbst geprueft, nicht gegen einen
            # abgeschriebenen Namen: taucht IRGENDEINES der neuen Felder auf,
            # ist es die neue Form. Damit kann diese Stelle nicht mehr
            # veralten, ohne dass die Eingriffskontrolle es zuerst meldet.
            strafe = 0.0
            if q:
                strafe += 6.0 if any(f in q for f in NEU_QUOTE) else 18.0
            if g:
                strafe += 4.0 if any(f in g for f in NEU_GUETE) else 12.0
            # DIE RICHTUNG HAENGT AM ANKER, NICHT AM AUFRUF (Reparatur
            # 10.08.). Vorher wurde sie aus dem Aufrufzaehler gewuerfelt -
            # damit bekam DERSELBE Anker in verschiedenen Armen verschiedene
            # Richtungen, und die gepaarte Richtungsauswertung pruefte Unsinn.
            # In echt waehlt das Modell fuer denselben Anker meist dieselbe
            # Richtung; der Umbau verschiebt sie nur an einem Teil der Faelle.
            schluessel = (sum(ord(c) * (k + 1) for k, c in enumerate(sym))
                          + int(preis * 1e6) % 9973)
            basis = ((schluessel * 40503) >> 8) % 100
            # Der ERWARTETE Effekt, gegen den die Auswertung geprueft wird:
            # die neue Fassung dreht einen Teil der SHORT-Faelle auf LONG.
            neue_form = (any(f in q for f in NEU_QUOTE)
                         or any(f in g for f in NEU_GUETE))
            kurz = basis < (35 - (8 if neue_form else 0))
            konf = 68 + ((n * 7) % 5) - 2 - (0 if kurz else strafe)
            r = -1.0 if kurz else 1.0
            s = 0.05 + streu * 0.04
            return {"action": "ERÖFFNEN", "richtung": "SHORT" if kurz else "LONG",
                    "_modell": "trocken", "confidence_pct": konf,
                    "hebel_vorschlag": 3.0,
                    "eigene_einschaetzung": {"folgen": "mit_vorbehalt", "kurzfazit": "x"},
                    "forecast": {"bull": {"scenario": "b", "probability_pct": 30},
                                 "base": {"scenario": "b", "probability_pct": 40},
                                 "bear": {"scenario": "b", "probability_pct": 30}},
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (1 - r * s),
                                  "usd_bis": preis * (1 - r * s)},
                    "take_profit": {"usd_von": preis * (1 + r * s * 2.2),
                                    "usd_bis": preis * (1 + r * s * 2.2)}}
    else:
        import os

        import config as config_module
        from agent import llm_schema
        from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
        config_module.load_env()
        if args.anbieter == "openrouter":
            from api.openrouter import OpenRouterClient
            client = OpenRouterClient(os.environ["OPENROUTER_API_KEY"])
        else:
            from api.gemini import DEFAULT_MODEL, GeminiClient
            client = GeminiClient(os.environ["GEMINI_API_KEY"])
            modell = args.modell or DEFAULT_MODEL
            stand = client.budget_status(modell)
            print(f"\nTagesbudget {modell}: {stand['verbraucht']} von "
                  f"{stand['budget']} verbraucht ({stand['tag_pazifik']}, "
                  f"Pazifik), {stand['verfuegbar']} frei")
            # Der Bedarf steht VOR dem Lauf fest - also auch vorher pruefen,
            # ob er hineinpasst. Am 09.08. lief ein Lauf drei Stunden gegen ein
            # leeres Budget, weil niemand vorher gerechnet hat.
            bedarf = args.anker * 5
            if stand["verfuegbar"] < bedarf:
                print(f"[FEHLER] Bedarf {bedarf} Aufrufe, verfuegbar "
                      f"{stand['verfuegbar']}. ABBRUCH - ein angefangener Lauf "
                      f"waere weder auswertbar noch umsonst.")
                return 1
        fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
        # Den Anbieter NICHT hartkodiert nennen - eine Anzeige, die "gemini"
        # sagt, waehrend OpenRouter laeuft, ist der Anfang eines falschen
        # Schlusses. Genau das ist am 09.08. passiert.
        print(f"\nAnbieter {args.anbieter}"
              + (f" / {args.modell}" if args.modell else "")
              + f", Antwortformat {fmt.get('type')}")

        def frage(fakten, sym):
            letzter = None
            for _ in range(3):
                time.sleep(args.pause)
                try:
                    zusatz = ({"model": args.modell}
                              if args.modell and args.anbieter == "gemini"
                              else {})
                    roh = client.chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user",
                          "content": json.dumps(fakten, ensure_ascii=False)}],
                        temperature=0.2, response_format=fmt, **zusatz)
                    return _validate_hebel(json.loads(roh), sym)
                except (json.JSONDecodeError, ValueError) as exc:
                    letzter = exc
            raise letzter

    ergebnis = {a: [] for a in ARME}
    fehler = Counter()
    beginn = time.time()
    for nr, (phase, label, sym, i) in enumerate(anker, 1):
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            continue
        for arm in ARME:
            try:
                antwort = frage(baue_arm(basis, arm, label, quote_neu, quote_alt,
                                         guete_neu, guete_alt), sym)
            except Exception as exc:  # noqa: BLE001
                fehler[type(exc).__name__] += 1
                continue
            z = M._zeile(sym, reihen[sym], i, antwort, arm, label)
            z["phase"] = phase
            ergebnis[arm].append(z)
        if nr % 5 == 0 or nr == len(anker):
            je = (time.time() - beginn) / max(1, nr)
            print(f"  Anker {nr:3}/{len(anker)}  "
                  + " ".join(f"{a}{len(ergebnis[a]):3}" for a in ARME)
                  + f"  Fehler {sum(fehler.values()):3}  {je:4.1f} s  "
                    f"Rest ~{(len(anker)-nr)*je/60:3.0f} min")
            # NICHT "laeuft es noch", sondern "kommt etwas heraus" (Nutzer-
            # Vorgabe 09.08.). Der Lauf vom selben Tag meldete "15 von 36,
            # null Fehler" und war zu diesem Zeitpunkt laengst nicht mehr
            # auswertbar - die LONG-Zellen standen bei n=1. Gegen die echten
            # Daten schlaegt diese Pruefung nach FUENF Ankern an.
            urteil = pruefe_auswertbarkeit(
                ergebnis, grundlinie="A1", geplant=len(anker), bisher=nr,
                richtungen_noetig=args.richtungen_noetig)
            if urteil.zeilen and (not urteil.tragfaehig or nr % 15 == 0):
                print(urteil.bericht())
            if not urteil.tragfaehig and not args.trotzdem_weiter:
                print("  Abbruch. Mit --trotzdem-weiter laesst sich das "
                      "uebergehen - dann aber bewusst.")
                break

    def nur(arm: str, richtung: str | None):
        return [x for x in ergebnis[arm]
                if richtung is None or x.get("richtung") == richtung]

    def wirkung(arm: str, richtung: str | None = None):
        d, s = _gepaart(nur("A1", richtung), nur(arm, richtung), "konfidenz")
        return (statistics.fmean(d) if d else None), len(d)

    def besserung_mit_unsicherheit(alt: str, neu: str, richtung: str | None):
        """Die Besserung MIT Streuung ueber Symbole - nicht als nackte Zahl.

        WARUM DIREKT alt GEGEN neu (2026-08-10). Die Regel fragt nach dem
        Unterschied ZWISCHEN den beiden Fassungen. Ihn als Differenz zweier
        Mittelwerte gegen A1 zu bilden, stimmt nur, solange beide Arme auf
        exakt denselben Ankern gepaart sind - faellt in einem Arm eine Zelle
        aus, vergleicht man zwei verschieden zusammengesetzte Mengen. Direkt
        gepaart kann das nicht passieren.

        WARUM MIT INTERVALL. Bis zum 09.08. lautete das Urteil `besserung >
        Rauschboden` - ein Mittelwert gegen eine feste Zahl, ohne jede
        Angabe, wie sicher dieser Mittelwert ist. Der Rauschboden misst die
        Wiederholstreuung EINER Antwort; er sagt nichts darueber, wie stark
        der Effekt zwischen SYMBOLEN schwankt. Genau diese Schwankung ist
        hier die Fehlerquelle, und `_gepaart` liefert die Symbolzuordnung
        laengst mit - sie wurde bisher weggeworfen.

        Cluster-Bootstrap ueber Symbole plus Wild-Cluster-p-Wert, weil wir mit
        rund 17 Symbolen genau in dem Bereich liegen, fuer den
        Cameron/Gelbach/Miller das Ueber-Ablehnen zeigen."""
        return _vergleich(nur(alt, richtung), nur(neu, richtung), "konfidenz")

    def traegt_ein_symbol_alles(alt: str, neu: str, richtung: str | None):
        """Bricht die Besserung zusammen, wenn EIN Symbol wegfaellt?

        Stehende Vorgabe: kein einzelnes Symbol darf einen Effekt tragen. Ohne
        diese Pruefung kann ein einziger Ausreisser - ein Rohstoff mit
        kaputter Kursreihe, ein Wert mit extremer Volatilitaet - ein Urteil
        allein herbeifuehren. Hier wird jedes Symbol einmal weggelassen und
        der groesste Ausschlag berichtet."""
        d, s = _gepaart(nur(alt, richtung), nur(neu, richtung), "konfidenz")
        if len(set(s)) < 3:
            return None
        gesamt = statistics.fmean(d)
        schlimmste, wert = None, gesamt
        for weg in set(s):
            rest = [x for x, sym in zip(d, s) if sym != weg]
            if len(rest) < 2:
                continue
            ohne = statistics.fmean(rest)
            if abs(ohne - gesamt) > abs(wert - gesamt):
                schlimmste, wert = weg, ohne
        return {"gesamt": gesamt, "ohne_symbol": schlimmste, "dann": wert,
                "symbole": len(set(s))}

    print("\n" + "=" * 76)
    print("KONFIDENZ-WIRKUNG gegen die Grundlinie A1, getrennt nach Richtung")
    print(f"{'Arm':10} {'LONG':>18} {'SHORT':>18} {'gesamt':>18}")
    kz = {}
    for arm in ARME[1:]:
        zeile = f"{arm:10}"
        kz[arm] = {}
        for ri in ("LONG", "SHORT", None):
            w, n = wirkung(arm, ri)
            kz[arm][ri or "gesamt"] = {"wirkung": w, "n": n}
            zeile += f" {(f'{w:+7.2f} (n={n:2})' if w is not None else '      - '):>18}"
        print(zeile)

    # DIE RICHTUNGSWAHL SELBST - ergaenzt am 10.08., vor dem Lauf.
    #
    # WARUM DAS DIE EIGENTLICHE FRAGE IST. Der Deadloop besteht darin, dass
    # keine LONG-Signale ENTSTEHEN - nicht darin, dass ihre Konfidenz zu
    # niedrig ausfaellt. Die Konfidenz ist ein Stellvertreter; die
    # Richtungswahl ist das Ziel. Sie wurde bisher gar nicht ausgewertet.
    #
    # UND SIE IST UNBEDINGT MESSBAR. Der Konfidenzvergleich je Richtung muss
    # auf Anker einschraenken, bei denen BEIDE Fassungen dieselbe Richtung
    # gewaehlt haben - er bedingt damit auf ein Ergebnis, das die Behandlung
    # selbst beeinflusst, und verliert genau die Faelle, in denen der Umbau am
    # meisten bewirkt hat. Der LONG-Anteil kennt dieses Problem nicht.
    print("\n" + "=" * 76)
    print("RICHTUNGSWAHL - das eigentliche Ziel, ungefiltert")
    anteile = {}
    for arm in ARME:
        zeilen_arm = ergebnis[arm]
        n_long = sum(1 for z in zeilen_arm if z.get("richtung") == "LONG")
        anteile[arm] = (n_long / len(zeilen_arm) * 100) if zeilen_arm else None
        print(f"  {arm:8} LONG {n_long:3} von {len(zeilen_arm):3} = "
              + (f"{anteile[arm]:5.1f} %" if anteile[arm] is not None else "  -"))

    def richtungswechsel(alt: str, neu: str) -> dict:
        """Wie viele Anker wechseln die Richtung - und in welche?"""
        idx = {(z["symbol"], z["datum"]): z.get("richtung") for z in ergebnis[alt]}
        nach_long = nach_short = gleich = 0
        for z in ergebnis[neu]:
            vorher = idx.get((z["symbol"], z["datum"]))
            if vorher is None:
                continue
            jetzt = z.get("richtung")
            if vorher == jetzt:
                gleich += 1
            elif jetzt == "LONG":
                nach_long += 1
            elif vorher == "LONG":
                nach_short += 1
        return {"nach_LONG": nach_long, "nach_SHORT": nach_short,
                "unveraendert": gleich}

    for alt, neu, name in (("Q_alt", "Q_neu", "Trefferquote"),
                           ("G_alt", "G_neu", "Systemguete")):
        w = richtungswechsel(alt, neu)
        netto = w["nach_LONG"] - w["nach_SHORT"]
        print(f"  {name}: {w['nach_LONG']} Anker wechseln zu LONG, "
              f"{w['nach_SHORT']} zu SHORT, {w['unveraendert']} unveraendert "
              f"-> netto {netto:+d} LONG")
        kz.setdefault("_richtung", {})[name] = {
            "wechsel": w, "netto_long": netto,
            "anteil_alt": anteile.get(alt), "anteil_neu": anteile.get(neu)}

    print("\n=== URTEIL nach der vorab festgelegten Regel ===")
    for alt, neu, name in (("Q_alt", "Q_neu", "Trefferquote"),
                           ("G_alt", "G_neu", "Systemguete")):
        wl_a = kz[alt]["LONG"]["wirkung"]
        wl_n = kz[neu]["LONG"]["wirkung"]
        ws_a = kz[alt]["SHORT"]["wirkung"]
        ws_n = kz[neu]["SHORT"]["wirkung"]
        if wl_a is None or wl_n is None:
            print(f"  {name}: zu wenige gepaarte LONG-Faelle")
            continue
        # Direkt gepaart statt als Differenz zweier Mittelwerte - und mit
        # Intervall statt als nackte Zahl (siehe Funktionsdokumentation).
        v_long = besserung_mit_unsicherheit(alt, neu, "LONG")
        v_short = besserung_mit_unsicherheit(alt, neu, "SHORT")
        konz = traegt_ein_symbol_alles(alt, neu, "LONG")
        besserung = v_long["wirkung"] if v_long else (wl_n - wl_a)
        short_drift = v_short["wirkung"] if v_short else None
        print(f"  {name}: LONG {wl_a:+.2f} -> {wl_n:+.2f}  "
              f"Besserung {besserung:+.2f}"
              + (f"   SHORT-Drift {short_drift:+.2f}" if short_drift is not None
                 else "   SHORT nicht vergleichbar"))
        if v_long:
            print(f"      95%-Intervall ueber {v_long['symbole']} Symbole "
                  f"[{v_long['ci_unten']:+.2f}, {v_long['ci_oben']:+.2f}], "
                  f"Wild-Cluster-p {v_long['wild_p']}")
        if konz and konz["ohne_symbol"]:
            print(f"      ohne {konz['ohne_symbol']}: {konz['dann']:+.2f} "
                  f"(statt {konz['gesamt']:+.2f})")
        kz.setdefault("_nachweis", {})[name] = {
            "long": v_long, "short": v_short, "konzentration": konz}

        # DIE REGEL, ergaenzt VOR dem Lauf am 10.08. und danach nicht mehr
        # angefasst: zur bisherigen Bedingung (Besserung ueber dem
        # Rauschboden) kommt, dass das 95-%-Intervall die Null NICHT
        # einschliessen darf. Das ist strenger als vorher, nicht lockerer -
        # bisher konnte ein Mittelwert ohne jede Streuungsangabe ein "WIRKSAM"
        # ausloesen.
        interval_traegt = v_long is None or (v_long["ci_unten"] or 0) > 0
        if besserung > boden and not interval_traegt:
            print(f"    -> NICHT nachweisbar: die Besserung liegt zwar ueber "
                  f"dem Rauschboden, aber das 95-%-Intervall schliesst die "
                  f"Null ein. Ueber Symbole hinweg ist der Effekt nicht "
                  f"stabil.")
            continue
        if konz and konz["ohne_symbol"] and besserung > boden:
            if (konz["dann"] - konz["gesamt"]) * (1 if konz["gesamt"] > 0 else -1) < 0 \
                    and abs(konz["dann"]) < boden:
                print(f"    -> NICHT nachweisbar: ohne das einzelne Symbol "
                      f"{konz['ohne_symbol']} faellt die Besserung auf "
                      f"{konz['dann']:+.2f} und damit unter den Rauschboden. "
                      f"Ein Symbol traegt das Ergebnis.")
                continue
        if besserung > boden:
            if short_drift is None:
                # KORREKTUR 09.08. abends. Hier stand vorher dasselbe
                # "WIRKSAM: ... SHORT bleibt" wie im vollstaendig geprueften
                # Fall - eine Behauptung ueber SHORT, die gar nicht geprueft
                # WERDEN konnte. Ein halbes Ergebnis las sich damit wie ein
                # ganzes. Die vorab festgelegte Regel hat zwei Bedingungen;
                # ist eine davon nicht pruefbar, ist sie nicht erfuellt,
                # sondern offen.
                print("    -> WIRKSAM AUF LONG, ABER die SHORT-Kontrolle war "
                      "nicht pruefbar (keine gepaarten SHORT-Zellen). Die "
                      "Regel ist damit zur HAELFTE erfuellt: ob der Umbau "
                      "die Asymmetrie aufloest oder nur verschiebt, ist "
                      "offen.")
            elif short_drift < -boden:
                print("    -> WIRKSAM, ABER: SHORT bewegt sich gegenlaeufig. "
                      "Die Asymmetrie waere gedreht, nicht aufgeloest.")
            else:
                print("    -> WIRKSAM: LONG wird weniger gedrueckt, SHORT bleibt.")
        else:
            print("    -> NICHT nachweisbar (Besserung unter dem Rauschboden).")

    if fehler:
        print(f"\nFehler: {dict(fehler)}")
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"kennzahlen": kz, "zeilen": ergebnis, "fehler": dict(fehler),
                    "quote_neu": quote_neu, "guete_neu": guete_neu,
                    "rauschboden": boden,
                    "anbieter": args.anbieter},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
