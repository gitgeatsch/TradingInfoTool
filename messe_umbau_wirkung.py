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
from messe_kettennaht_eingriffe import _gepaart
from pruefe_auswertbarkeit import pruefe_auswertbarkeit
import messe_regimephasen_llm as M

ARME = ("A1", "Q_alt", "Q_neu", "G_alt", "G_neu")

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
    anker = []
    for phase in M.ARME:
        for sym, i in je_phase[phase]:
            anker.append((phase, M.LABEL[phase], sym, i))
    anker.sort(key=lambda x: (reihen[x[2]][x[3]].date, x[2]))
    if len(anker) > args.anker:
        anker = anker[::max(1, len(anker) // args.anker)][:args.anker]

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
            strafe = 0.0
            if q:
                strafe += 6.0 if "geschrumpft" in q else 18.0
            if g:
                strafe += 4.0 if "signalbeitrag_r" in g else 12.0
            kurz = (((n * 40503) >> 8) % 100) < 35
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
            from api.gemini import GeminiClient
            client = GeminiClient(os.environ["GEMINI_API_KEY"])
        fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
        # Den Anbieter NICHT hartkodiert nennen - eine Anzeige, die "gemini"
        # sagt, waehrend OpenRouter laeuft, ist der Anfang eines falschen
        # Schlusses. Genau das ist am 09.08. passiert.
        print(f"\nAnbieter {args.anbieter}, Antwortformat {fmt.get('type')}")

        def frage(fakten, sym):
            letzter = None
            for _ in range(3):
                time.sleep(args.pause)
                try:
                    roh = client.chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user",
                          "content": json.dumps(fakten, ensure_ascii=False)}],
                        temperature=0.2, response_format=fmt)
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

    def wirkung(arm: str, richtung: str | None = None):
        za = [x for x in ergebnis["A1"]
              if richtung is None or x.get("richtung") == richtung]
        zb = [x for x in ergebnis[arm]
              if richtung is None or x.get("richtung") == richtung]
        d, s = _gepaart(za, zb, "konfidenz")
        return (statistics.fmean(d) if d else None), len(d)

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
        besserung = wl_n - wl_a
        short_drift = (ws_n - ws_a) if (ws_a is not None and ws_n is not None) else None
        print(f"  {name}: LONG {wl_a:+.2f} -> {wl_n:+.2f}  "
              f"Besserung {besserung:+.2f}"
              + (f"   SHORT-Drift {short_drift:+.2f}" if short_drift is not None
                 else "   SHORT nicht vergleichbar"))
        if besserung > boden:
            if short_drift is not None and short_drift < -boden:
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
