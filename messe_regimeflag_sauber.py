"""Der Regime-Flag, sauber: 2x2 aus Trigger-Richtung und Flag (2026-08-09).

WARUM EIN ZWEITER ANLAUF. Der erste Versuch (`messe_kettennaht_eingriffe.py`,
Arm E2) hat den Flag OHNE Trigger-Richtung eingespeist. Der Flag bedeutet aber
"die Richtung des Kandidaten steht dem Regime entgegen" - ohne genannte
Richtung ist das mehrdeutig, und das Modell hat sie sich daraus rekonstruiert:
im BULLE-Arm kippten 10 von 12 Faellen von LONG auf SHORT. Die gepaarten
Konfidenzdifferenzen blieben gueltig, aber die Richtungszusammensetzung war
verschoben - eine Aussage ueber "wen bestraft der Flag" war daraus nicht
ableitbar.

DIE FRAGE, die dieser Lauf entscheidet:

    Ist der Flag ein RICHTUNGSFILTER (bestraft immer LONG)
    oder ein TREND-KONFLIKT-Mechanismus (bestraft die trendabgewandte Seite)?

Produktiv entsteht er als
    (regime=="baer" and trigger=="LONG") or (regime=="bulle" and trigger=="SHORT")
also symmetrisch. Dass er faktisch immer LONG trifft, liegt allein daran, dass
das Regime in der gesamten Historie "baer" war.

DIE VIER ARME, alle auf denselben Ankern, gepaart:

    T1   trigger.richtung = LONG,  kein Flag
    T2   trigger.richtung = LONG,  Flag = true
    T3   trigger.richtung = SHORT, kein Flag
    T4   trigger.richtung = SHORT, Flag = true

Der Trigger steht in ALLEN vier Armen - er ist Teil der Grundlinie, nicht des
Eingriffs. Nur der Flag variiert. Damit misst T2-T1 die Flagwirkung bei einem
LONG-Kandidaten und T4-T3 dieselbe bei einem SHORT-Kandidaten.

VORHERSAGEN, vor dem Lauf festgelegt:

    TREND-KONFLIKT:  im BAER-Regime ist T2-T1 stark negativ und T4-T3 nahe null;
                     im BULLE-Regime umgekehrt.
    RICHTUNGSFILTER: T2-T1 ist in JEDEM Regime negativ, T4-T3 in keinem.

RAUSCHBODEN: uebernommen aus dem Kettennaht-Lauf desselben Tages, desselben
Anbieters und derselben Ankermenge - **0,83 Konfidenzpunkte** (A1 gegen A2,
n=36). Ihn hier erneut zu messen waere ein zweiter Arm ohne Erkenntnisgewinn;
das Kontingent ist begrenzt und der Wert ist frisch.

REGIME-LABEL: die tatsaechliche Marktphase des Ankers. Einem Bullen-Anker
"baer" zu erzaehlen waere eine falsche Information - und genau die Variation
ueber die Regimes ist hier der Punkt, weil der Flag regimeabhaengig wirken
SOLL.

    python messe_regimeflag_sauber.py --anker 36 --trocken
    python messe_regimeflag_sauber.py --anker 36 --ausgabe regimeflag.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time
from collections import Counter, defaultdict

from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
from messe_kettennaht_eingriffe import REGIME_FLAG_HINWEIS, _gepaart
import messe_regimephasen_llm as M

ARME = ("T1_long_ohne", "T2_long_flag", "T3_short_ohne", "T4_short_flag")
TRIGGER = {"T1_long_ohne": "LONG", "T2_long_flag": "LONG",
           "T3_short_ohne": "SHORT", "T4_short_flag": "SHORT"}
MIT_FLAG = {"T2_long_flag", "T4_short_flag"}

# Aus dem Kettennaht-Lauf vom selben Tag, Anbieter und Ankersatz.
RAUSCHBODEN_KONFIDENZ = 0.83


def baue_arm(fakten: dict, arm: str, label: str) -> dict:
    neu = json.loads(json.dumps(fakten))
    neu["regime"] = dict(neu.get("regime") or {})
    neu["regime"]["wert"] = label
    neu["regime"]["quelle"] = "historische EMA-Ordnung des BTC am Ankertag"
    # Der Trigger gehoert in ALLE Arme - er ist Grundlinie, nicht Eingriff.
    # Sonst misst T2-T1 zwei Aenderungen auf einmal.
    neu["trigger"] = {"richtung": TRIGGER[arm],
                      "quelle": "Screening-Kandidat (historisch gesetzt)"}
    if arm in MIT_FLAG:
        neu["regime"]["richtungs_konflikt_mit_trigger"] = True
        neu["regime"]["richtungs_konflikt_hinweis"] = REGIME_FLAG_HINWEIS
    return neu


def pruefe_eingriffe(basis: dict, label: str) -> list[tuple[str, bool, str]]:
    aus = []
    for arm in ARME:
        b = baue_arm(basis, arm, label)
        aus.append((f"{arm}: Trigger-Richtung {TRIGGER[arm]}",
                    (b.get("trigger") or {}).get("richtung") == TRIGGER[arm], ""))
        soll = arm in MIT_FLAG
        ist = b["regime"].get("richtungs_konflikt_mit_trigger") is True
        aus.append((f"{arm}: Flag {'true' if soll else 'abwesend'}", ist == soll, ""))
    # Die Paare duerfen sich AUSSCHLIESSLICH im Flag unterscheiden.
    for a, b in (("T1_long_ohne", "T2_long_flag"),
                 ("T3_short_ohne", "T4_short_flag")):
        fa, fb = baue_arm(basis, a, label), baue_arm(basis, b, label)
        fa["regime"].pop("richtungs_konflikt_mit_trigger", None)
        fa["regime"].pop("richtungs_konflikt_hinweis", None)
        fb["regime"].pop("richtungs_konflikt_mit_trigger", None)
        fb["regime"].pop("richtungs_konflikt_hinweis", None)
        aus.append((f"{a} und {b} unterscheiden sich NUR im Flag",
                    json.dumps(fa, sort_keys=True) == json.dumps(fb, sort_keys=True),
                    ""))
    return aus


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=36)
    p.add_argument("--je-symbol", type=int, default=5)
    p.add_argument("--pause", type=float, default=0.2)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="regimeflag.json")
    args = p.parse_args()

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

    print(f"Anker {len(anker)}, {len({a[2] for a in anker})} Symbole")
    print(f"Phasen: {dict(Counter(a[0] for a in anker))}")
    print(f"{len(ARME)} Arme -> {len(anker) * len(ARME)} Aufrufe")
    print(f"\nRauschboden (uebernommen): {RAUSCHBODEN_KONFIDENZ:.2f} Konfidenzpunkte")
    print("VORHERSAGE Trend-Konflikt: im BAER ist T2-T1 stark negativ und T4-T3")
    print("nahe null; im BULLE umgekehrt.")
    print("VORHERSAGE Richtungsfilter: T2-T1 in JEDEM Regime negativ, T4-T3 nie.")

    print("\n=== EINGRIFFSKONTROLLE ===")
    probe = baue_historische_fakten(anker[0][2], reihen[anker[0][2]], anker[0][3], btc)
    alles = True
    for name, ok, detail in pruefe_eingriffe(probe, anker[0][1]):
        print(f"  {'[ok]    ' if ok else '[FEHLER]'} {name}")
        alles &= ok
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT
    for feld in ("richtungs_konflikt_mit_trigger", "trigger"):
        drin = feld in SYSTEM_PROMPT
        print(f"  {'[ok]    ' if drin else '[FEHLER]'} Prompt nennt {feld}")
        alles &= drin
    if not alles:
        print("\n  ABBRUCH: Eingriff kommt nicht an oder hat keinen Wirkungspfad.")
        return 2

    if args.trocken:
        # NICHT `z` nennen: die Ergebnisschleife unten benutzt `z` fuer die
        # Ergebniszeile und ueberschreibt den Zaehler sonst ab dem zweiten
        # Aufruf - dann laeuft `z[0] += 1` auf einem Dict und wirft KeyError.
        # Genau das ist im ersten Trockenlauf passiert: 95 von 96 Aufrufen weg.
        zaehler = [0]

        def frage(fakten, sym):
            zaehler[0] += 1
            n = zaehler[0]
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            streu = ((n * 2654435761) >> 16) % 100 / 100.0
            flag = bool(fakten["regime"].get("richtungs_konflikt_mit_trigger"))
            tr = fakten["trigger"]["richtung"]
            reg = fakten["regime"]["wert"]
            # Mock bildet den TREND-KONFLIKT nach, damit die Auswertung an einem
            # Fall mit bekannter Antwort geprueft wird.
            konflikt = flag and ((reg == "baer" and tr == "LONG")
                                 or (reg == "bulle" and tr == "SHORT"))
            konf = 68 + ((n * 7) % 5) - 2 - (15 if konflikt else 0)
            kurz = tr == "SHORT"
            r = -1.0 if kurz else 1.0
            s = 0.05 + streu * 0.04
            return {"action": "ERÖFFNEN", "richtung": tr, "_modell": "trocken",
                    "confidence_pct": konf, "hebel_vorschlag": 3.0 - (1.0 if konflikt else 0),
                    "eigene_einschaetzung": {"folgen": "mit_vorbehalt", "kurzfazit": "x"},
                    "forecast": {"bull": {"scenario": "b", "probability_pct": 30},
                                 "base": {"scenario": "b", "probability_pct": 40},
                                 "bear": {"scenario": "b", "probability_pct": 30}},
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (1 - r * s), "usd_bis": preis * (1 - r * s)},
                    "take_profit": {"usd_von": preis * (1 + r * s * 2.2),
                                    "usd_bis": preis * (1 + r * s * 2.2)}}
    else:
        import os

        import config as config_module
        from agent import llm_schema
        from agent.krypto.hebel_analyst import _validate_hebel
        from api.gemini import GeminiClient
        config_module.load_env()
        client = GeminiClient(os.environ["GEMINI_API_KEY"])
        fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
        print(f"\nAnbieter gemini, Antwortformat {fmt.get('type')}")

        def frage(fakten, sym):
            letzter = None
            for _ in range(3):
                time.sleep(args.pause)
                try:
                    roh = client.chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}],
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
                antwort = frage(baue_arm(basis, arm, label), sym)
            except Exception as exc:  # noqa: BLE001
                fehler[type(exc).__name__] += 1
                continue
            z = M._zeile(sym, reihen[sym], i, antwort, arm, label)
            z["phase"] = phase
            z["trigger_richtung"] = TRIGGER[arm]
            ergebnis[arm].append(z)
        if nr % 6 == 0 or nr == len(anker):
            je = (time.time() - beginn) / max(1, nr)
            print(f"  Anker {nr:3}/{len(anker)}  "
                  + " ".join(f"{a.split('_')[0]}{len(ergebnis[a]):3}" for a in ARME)
                  + f"  Fehler {sum(fehler.values()):3}  {je:4.1f} s  "
                    f"Rest ~{(len(anker)-nr)*je/60:3.0f} min")

    def diff(a: str, b: str, phase: str | None = None) -> tuple[float | None, int]:
        za = [x for x in ergebnis[a] if phase is None or x["phase"] == phase]
        zb = [x for x in ergebnis[b] if phase is None or x["phase"] == phase]
        d, _ = _gepaart(za, zb, "konfidenz")
        return (statistics.fmean(d) if d else None), len(d)

    print("\n" + "=" * 78)
    print("FLAGWIRKUNG je Regime - hier entscheidet sich Richtungsfilter gegen Trend-Konflikt")
    print(f"{'Regime':12} {'LONG-Trigger (T2-T1)':>24} {'SHORT-Trigger (T4-T3)':>24}")
    for phase in ("BULLE", "SEITWAERTS", "BAER"):
        dl, nl = diff("T1_long_ohne", "T2_long_flag", phase)
        ds, ns = diff("T3_short_ohne", "T4_short_flag", phase)
        print(f"{phase:12} "
              f"{(f'{dl:+8.2f} (n={nl})' if dl is not None else '       - '):>24} "
              f"{(f'{ds:+8.2f} (n={ns})' if ds is not None else '       - '):>24}")
    dl, nl = diff("T1_long_ohne", "T2_long_flag")
    ds, ns = diff("T3_short_ohne", "T4_short_flag")
    print(f"{'GESAMT':12} "
          f"{(f'{dl:+8.2f} (n={nl})' if dl is not None else '       - '):>24} "
          f"{(f'{ds:+8.2f} (n={ns})' if ds is not None else '       - '):>24}")

    print(f"\nMassstab: Rauschboden {RAUSCHBODEN_KONFIDENZ:.2f} Punkte.")
    print("TREND-KONFLIKT gilt, wenn die Strafe dem Regime folgt (im BAER auf")
    print("LONG, im BULLE auf SHORT). RICHTUNGSFILTER gilt, wenn nur die")
    print("LONG-Spalte negativ ist - in JEDEM Regime.")
    if fehler:
        print(f"\nFehler: {dict(fehler)}")
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"zeilen": ergebnis, "rauschboden": RAUSCHBODEN_KONFIDENZ,
                    "fehler": dict(fehler)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
