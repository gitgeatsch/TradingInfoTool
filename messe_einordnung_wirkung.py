"""Wirkt das KLARTEXT-Urteil oder der Zahlenvergleich?

DER BEFUND, DER DAZU FUEHRT (Lauf A, 10.08., n=50): die neue Systemguete-Form
verschlechtert die LONG-Wahl messbar - Konfidenz -3,85 auf -8,86, Intervall
[-9,41; -2,17], Wild-Cluster-p 0,02, Richtungswahl 56 % auf 44 %. Sieben Anker
wechseln zu SHORT, einer zu LONG.

DIE FRAGE. Der Umbau bringt zwei verschiedene Dinge in den Prompt:

  1. Einen ZAHLENVERGLEICH: Basislinie -0,094 R, Signalbeitrag -0,055 R,
     Konfidenzintervall, Aufloesungsquote, geschrumpfte Werte.
  2. Ein KLARTEXT-URTEIL: `einordnung: "unter der Basislinie"`.

Die Schrumpfung selbst scheidet als Ursache aus: bei n=133 und k=50 liegt das
Gewicht bei 0,727, der Wert wandert von -0,149 auf -0,134. Sie sollte vor
harten Urteilen auf DUENNER Datenlage schuetzen - die Datenlage ist nicht
duenn, also schuetzt sie vor nichts. Sie ist inert, nicht schaedlich.

Bleiben die beiden oben. Diese Messung trennt sie:

    Arm MIT     der Systemguete-Fakt, wie Lauf A ihn verwendet hat
    Arm OHNE    derselbe Fakt, nur ohne die Zeile `einordnung`

Alles andere bitgleich, dieselben Anker, gepaart. Ein Unterschied kann dann
nur an dieser einen Zeile liegen.

WOZU DIE ANTWORT TAUGT. Wirkt der Klartext, ist die Lehre allgemein: ein
Werturteil im Faktensatz wiegt schwerer als die Zahlen, aus denen es stammt -
und das betrifft jedes Feld, das wir je als `einordnung` formuliert haben.
Wirkt er nicht, liegt es am Zahlenvergleich, und die Rueoecknahme muss anders
aussehen.

    python messe_einordnung_wirkung.py --anker 25
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys
import time
from collections import Counter

import messe_regimephasen_llm as M
from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
from messe_kettennaht_eingriffe import _gepaart


VORGABE_DB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
              "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
              "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=25)
    p.add_argument("--je-symbol", type=int, default=5)
    p.add_argument("--pause", type=float, default=0.2)
    p.add_argument("--modell", default="gemini-3.1-flash-lite")
    p.add_argument("--db", default=VORGABE_DB)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="einordnung.json")
    args = p.parse_args()

    from messe_umbau_wirkung import (hole_echte_fakten, verschraenke_phasen)
    _, guete_neu = hole_echte_fakten(args.db)
    if not guete_neu:
        print("Systemguete-Fakt nicht baubar - Abbruch.")
        return 1
    guete_ohne = {k: v for k, v in guete_neu.items() if k != "einordnung"}

    reihen = lade_reihen()
    btc = reihen["BTC"]
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.anker, args.je_symbol)
    anker = verschraenke_phasen(je_phase, M.ARME, M.LABEL, reihen, args.anker)
    print(f"Anker {len(anker)}, {len({a[2] for a in anker})} Symbole, "
          f"Phasen {dict(Counter(a[0] for a in anker))}")

    print("\n=== EINGRIFFSKONTROLLE ===")
    pruefungen = [
        ("MIT-Arm traegt die einordnung", "einordnung" in guete_neu,
         str(guete_neu.get("einordnung"))),
        ("OHNE-Arm traegt sie NICHT", "einordnung" not in guete_ohne, ""),
        ("sonst sind beide bitgleich",
         {k: v for k, v in guete_neu.items() if k != "einordnung"} == guete_ohne, ""),
        ("genau EIN Feld Unterschied",
         len(guete_neu) - len(guete_ohne) == 1,
         f"{len(guete_neu)} gegen {len(guete_ohne)}"),
        ("die ZAHLEN bleiben in beiden erhalten",
         all(k in guete_ohne for k in ("basislinie_erwartungswert_r",
                                       "signalbeitrag_r", "erwartungswert_ci",
                                       "erwartungswert_gewichtet")), ""),
    ]
    alles = True
    for name, ok, detail in pruefungen:
        print(f"  {'[ok]    ' if ok else '[FEHLER]'} {name}"
              + (f"   {detail}" if detail else ""))
        alles &= ok
    if not alles:
        print("\n  ABBRUCH: die Arme unterscheiden sich nicht wie beabsichtigt.")
        return 2

    if args.trocken:
        print("\nTrockenlauf - keine Aufrufe.")
        return 0

    import config as config_module
    from agent import llm_schema
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
    from api.gemini import GeminiClient
    config_module.load_env()
    client = GeminiClient(os.environ["GEMINI_API_KEY"])
    fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
    stand = client.budget_status(args.modell)
    bedarf = int(len(anker) * 2 * 1.35)
    print(f"\nModell {args.modell}, Format {fmt.get('type')}")
    print(f"Budget {stand['verbraucht']}/{stand['budget']}, "
          f"{stand['verfuegbar']} frei - Bedarf ~{bedarf}")
    if stand["verfuegbar"] < bedarf:
        print("[FEHLER] Budget reicht nicht. ABBRUCH.")
        return 1

    def frage(fakten, sym):
        letzter = None
        for _ in range(3):
            time.sleep(args.pause)
            try:
                roh = client.chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user",
                      "content": json.dumps(fakten, ensure_ascii=False)}],
                    temperature=0.2, response_format=fmt, model=args.modell)
                return _validate_hebel(json.loads(roh), sym)
            except Exception as exc:  # noqa: BLE001
                letzter = exc
        raise letzter

    ergebnis = {"mit": [], "ohne": []}
    fehler: Counter = Counter()
    beginn = time.time()
    for nr, (phase, label, sym, i) in enumerate(anker, 1):
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            continue
        for arm, fakt in (("mit", guete_neu), ("ohne", guete_ohne)):
            f = json.loads(json.dumps(basis))
            f["regime"] = dict(f.get("regime") or {})
            f["regime"]["wert"] = label
            f["regime"]["quelle"] = "historische EMA-Ordnung des BTC am Ankertag"
            f["systemguete"] = dict(fakt)
            try:
                antwort = frage(f, sym)
            except Exception as exc:  # noqa: BLE001
                fehler[type(exc).__name__] += 1
                continue
            z = M._zeile(sym, reihen[sym], i, antwort, arm, label)
            z["phase"] = phase
            ergebnis[arm].append(z)
        if nr % 5 == 0 or nr == len(anker):
            je = (time.time() - beginn) / max(1, nr)
            m = Counter(x.get("richtung") for x in ergebnis["mit"])
            o = Counter(x.get("richtung") for x in ergebnis["ohne"])
            print(f"  {nr:3}/{len(anker)}  mit {dict(m)}  ohne {dict(o)}  "
                  f"Fehler {sum(fehler.values())}  {je:.1f} s/Anker")

    print("\n" + "=" * 72)
    print("RICHTUNGSWAHL")
    for arm in ("mit", "ohne"):
        z = ergebnis[arm]
        n_long = sum(1 for x in z if x.get("richtung") == "LONG")
        print(f"  {arm:5s} LONG {n_long:3d} von {len(z):3d} = "
              + (f"{100 * n_long / len(z):5.1f} %" if z else "-"))

    idx = {(x["symbol"], x["datum"]): x.get("richtung") for x in ergebnis["mit"]}
    w = Counter()
    for x in ergebnis["ohne"]:
        vor = idx.get((x["symbol"], x["datum"]))
        if vor:
            w[(vor, x.get("richtung"))] += 1
    print("\nWECHSEL beim Entfernen der einordnung:")
    for (a, b), n in w.most_common():
        print(f"   {a:6s} -> {b:6s}  {n:3d}" + ("   (unveraendert)" if a == b else ""))
    nach_long = sum(n for (a, b), n in w.items() if b == "LONG" and a != "LONG")
    nach_short = sum(n for (a, b), n in w.items() if b == "SHORT" and a != "SHORT")

    d, s = _gepaart(ergebnis["mit"], ergebnis["ohne"], "konfidenz")
    print("\nKONFIDENZ (ohne minus mit, gepaart je Anker):")
    if d:
        print(f"   Mittel {statistics.fmean(d):+.2f} Punkte ueber {len(d)} "
              f"Paare / {len(set(s))} Symbole")
        try:
            from bewerte_fakt_wirkung import _cluster_bootstrap, _wild_cluster_p_wert
            u, o2 = _cluster_bootstrap(d, s)
            print(f"   95%-Intervall [{u:+.2f}, {o2:+.2f}], "
                  f"Wild-Cluster-p {_wild_cluster_p_wert(d, s)}")
        except Exception as exc:  # noqa: BLE001
            print(f"   (Intervall nicht berechenbar: {exc})")

    print("\n=== URTEIL ===")
    print(f"  Ohne die einordnung wechseln {nach_long} Anker zu LONG und "
          f"{nach_short} zu SHORT.")
    if nach_long > nach_short:
        print("  -> Das KLARTEXT-URTEIL unterdrueckt LONG. Die Zahlen allein "
              "tun es nicht. Lehre: ein Werturteil im Faktensatz wiegt "
              "schwerer als die Zahlen, aus denen es stammt.")
    elif nach_short > nach_long:
        print("  -> Unerwartet: ohne die einordnung waehlt das Modell "
              "SELTENER LONG. Der Klartext wirkte also daempfend auf SHORT.")
    else:
        print("  -> Kein Unterschied. Dann wirkt nicht der Klartext, sondern "
              "der Zahlenvergleich - die Ruecknahme muss dort ansetzen.")
    if fehler:
        print(f"\nFehler: {dict(fehler)}")
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"zeilen": ergebnis, "fehler": dict(fehler),
                    "guete_mit": guete_neu, "guete_ohne": guete_ohne},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
