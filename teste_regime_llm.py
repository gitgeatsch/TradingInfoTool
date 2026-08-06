"""Reagiert das LLM ueberhaupt auf das Regime? Drei-Arm-Test (06.08.)

DIE LUECKE. Der Trockenlauf `messe_regimewechsel_trockenlauf.py` hat die
DETERMINISTISCHE Haelfte des Regimewechsels vermessen (Gate-Schwellen,
Positionsgroessen-Sockel, Small-Cap-Budget, AZ-7). Die andere Haelfte fehlte:
das Regime steht auch im FAKTENSATZ - als `regime.wert` und als `regime_profil`
mit vier Gewichten, die KEINE Prompt-Regel erklaert (Katalog 4.2: "keine Regel,
kein Gate").

Da ausnahmslos jedes Signal der Historie `regime = "baer"` trug, ist das
Modellverhalten unter jedem anderen Regime **vollstaendig unbekannt**.

DREI ARME, alle mit IDENTISCHEM Prompt - die Aenderung sitzt in den Fakten:
    A1  Fakten unveraendert (regime = baer, heutiger Zustand)
    A2  identisch zu A1 - der Abstand ist der Rauschboden
    B   regime = seitwaerts, regime_profil auf das seitwaerts-Profil getauscht

WARUM SEITWAERTS UND NICHT KRISE_EXTREM. Der Trockenlauf zeigt, dass
krise_extrem die drastischere Gate-Wirkung hat (Durchlass 80 % -> 5,7 %, plus
AZ-7). Genau deshalb ist SEITWAERTS der informativere Test: dort ist die
Gate-Wirkung mild, also misst man ueberwiegend die LLM-Reaktion statt einen
Gate-Effekt. Bei krise_extrem wuerde das Gate den Grossteil ohnehin abfangen -
man saehe nicht, ob das Modell selbst anders urteilt.

MESSGROESSEN, gepaart je Faktensatz (alle Arme sehen denselben Fall):
    primaer    EROEFFNEN-Quote und Konfidenz - reagiert das Modell auf das Label?
    sekundaer  Stop-Abstand und CRV - aendert es auch die Zonen?

VORAB FESTGEHALTEN, damit es nicht nachtraeglich passend gemacht wird: ich
erwarte eine SCHWACHE bis KEINE Reaktion. Begruendung: die vier Gewichte haben
keine Regel, und `regime.wert` wird in Regel 3 nur fuer `krise_extrem` genannt
(IMMER HALTEN). Fuer den Uebergang baer -> seitwaerts sagt der Prompt nichts.
Ist die Reaktion dennoch stark, waere das ein wichtiger Fund - dann steuert ein
ungeregelter Fakt das Verhalten.

Liest echte Faktensaetze aus dem Export. Braucht MISTRAL_API_KEY.
"""
from __future__ import annotations

import copy
import io
import json
import os
import re
import statistics
import sys
from collections import defaultdict

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
ZIEL_REGIME = "seitwaerts"


def _arg(name: str, standard):
    if name in sys.argv:
        return type(standard)(sys.argv[sys.argv.index(name) + 1])
    return standard


def lade_faelle(n: int):
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    block = d.get("hebel_faktensaetze") or {}
    sig = {s["id"]: s for s in d["hebel_signals"]}
    kand = []
    for e in block.get("eintraege", []):
        grund = str(sig.get(e["id"], {}).get("gate_reason") or "")
        if "ltig" in grund and "ung" in grund.lower():
            continue
        kand.append(e)
    kand.sort(key=lambda e: (e["created_at"], e["symbol"]))
    schritt = max(1, len(kand) // n)
    versatz = _arg("--versatz", 0) % schritt
    return kand[versatz::schritt][:n]


def fakten_mit_regime(fakten: dict, regime: str, profile: dict) -> dict:
    """Regime im Faktensatz austauschen - Label UND Profil, wie im Betrieb.

    Beides gehoert zusammen: im Produktivcode kommt `regime_profil` aus
    config['regime']['profile'][regime]. Nur das Label zu tauschen waere ein
    Zustand, den es real nie gibt."""
    neu = copy.deepcopy(fakten)
    if isinstance(neu.get("regime"), dict):
        neu["regime"]["wert"] = regime
    prof = profile.get(regime) or {}
    if isinstance(neu.get("regime_profil"), dict):
        for schluessel in ("min_konfidenz_prozent", "small_cap_budget_prozent",
                           "gewicht_technik", "gewicht_fundamental",
                           "gewicht_momentum", "gewicht_kontext_makro"):
            if schluessel in prof:
                neu["regime_profil"][schluessel] = prof[schluessel]
    return neu


def stop_abstand(antwort) -> float | None:
    try:
        e = (antwort["entry"]["usd_von"] + antwort["entry"]["usd_bis"]) / 2.0
        short = str(antwort.get("richtung", "LONG")).upper() == "SHORT"
        st = antwort["stop_loss"]["usd_bis" if short else "usd_von"]
    except (KeyError, TypeError):
        return None
    if not e or e <= 0 or st is None:
        return None
    w = abs(e - st) / e * 100
    return w if 0 < w < 60 else None


def main() -> int:
    if not os.environ.get("MISTRAL_API_KEY"):
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    if not os.environ.get("MISTRAL_API_KEY"):
        raise SystemExit("MISTRAL_API_KEY fehlt")

    import config as config_module
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT
    from api.mistral import MistralClient
    from backtest_llm1_historisch import frage

    profile = config_module.load_config()["regime"]["profile"]
    n = _arg("--n", 12)
    w = _arg("--wdh", 1)
    faelle = lade_faelle(n)
    arme = {"A1 baer (heute)": None,
            "A2 baer (Rauschen)": None,
            f"B {ZIEL_REGIME}": ZIEL_REGIME}
    print(f"{len(faelle)} Faktensaetze x {len(arme)} Arme x {w} Wiederholungen = "
          f"{len(faelle)*len(arme)*w} Aufrufe")
    print(f"Prompt IDENTISCH in allen Armen - getauscht wird nur regime.wert "
          f"und regime_profil.")
    print(f"  baer      : min_konfidenz {profile['baer']['min_konfidenz_prozent']}, "
          f"Gewicht Technik {profile['baer']['gewicht_technik']}")
    print(f"  {ZIEL_REGIME}: min_konfidenz {profile[ZIEL_REGIME]['min_konfidenz_prozent']}, "
          f"Gewicht Technik {profile[ZIEL_REGIME]['gewicht_technik']}")

    client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
    akt = defaultdict(list)
    konf = defaultdict(list)
    stops = defaultdict(list)
    antworten = []

    for f in faelle:
        basis = json.loads(f["facts_json"])
        if not isinstance(basis.get("regime"), dict):
            print(f"  {f['symbol']}: kein regime-Block, uebersprungen")
            continue
        print(f"\n{f['symbol']} @ {f['created_at'][:16]} "
              f"(ist: {basis['regime'].get('wert')}):", flush=True)
        for name, ziel in arme.items():
            fakten = basis if ziel is None else fakten_mit_regime(basis, ziel, profile)
            zeile = []
            for _ in range(w):
                a = frage(client, fakten, SYSTEM_PROMPT)
                if not a:
                    continue
                akt[name].append(str(a.get("action", "?")).upper())
                c = a.get("confidence_pct")
                if isinstance(c, (int, float)):
                    konf[name].append((f["symbol"], float(c)))
                s = stop_abstand(a)
                if s is not None:
                    stops[name].append((f["symbol"], s))
                zeile.append(f"{a.get('action','?')[:4]}/{c}")
                antworten.append({"arm": name, "symbol": f["symbol"],
                                  "created_at": f["created_at"], "antwort": a})
            print(f"  {name:22s} {zeile}", flush=True)

    ziel_datei = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "data", "regime_llm_antworten.json")
    os.makedirs(os.path.dirname(ziel_datei), exist_ok=True)
    alt = []
    if os.path.exists(ziel_datei):
        try:
            alt = json.load(io.open(ziel_datei, encoding="utf-8"))
        except Exception:
            alt = []
    json.dump(alt + antworten, io.open(ziel_datei, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(antworten)} Antworten gespeichert ({len(alt)+len(antworten)} gesamt)")

    print()
    print("=" * 78)
    print("ERGEBNIS")
    print("=" * 78)
    for name in arme:
        a = akt[name]
        if not a:
            continue
        er = sum(1 for x in a if x == "ERÖFFNEN") / len(a) * 100
        k = [v for _, v in konf[name]]
        s = [v for _, v in stops[name]]
        print(f"  {name:22s} EROEFFNEN {er:5.1f} %  Konfidenz "
              f"{statistics.fmean(k) if k else float('nan'):5.1f}  "
              f"Stop {statistics.fmean(s) if s else float('nan'):5.2f} %  (n={len(a)})")

    print()
    print("  GEPAART (je Faktensatz, damit die Symbolstreuung herausfaellt):")
    for label, quelle in (("Konfidenz", konf), ("Stop-Abstand", stops)):
        je = defaultdict(dict)
        for name in arme:
            for sym, v in quelle[name]:
                je[sym].setdefault(name, []).append(v)
        namen = list(arme)
        paare_b, paare_rausch = [], []
        for sym, d_ in je.items():
            if all(n_ in d_ for n_ in namen):
                a1 = statistics.fmean(d_[namen[0]])
                a2 = statistics.fmean(d_[namen[1]])
                b = statistics.fmean(d_[namen[2]])
                paare_b.append(b - a1)
                paare_rausch.append(a2 - a1)
        if len(paare_b) >= 2:
            eff = statistics.fmean(paare_b)
            rausch = statistics.stdev(paare_rausch)
            se = statistics.stdev(paare_b) / (len(paare_b) ** 0.5)
            print(f"    {label:14s} Wirkung {eff:+7.3f}  SE {se:.3f}  "
                  f"t {eff/se if se else 0:+5.2f}  n={len(paare_b)}  "
                  f"RAUSCHBODEN {rausch:.3f}")
            if abs(eff) < rausch:
                print(f"    {'':14s} -> Effekt KLEINER als das Eigenrauschen zweier "
                      f"identischer Arme")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
