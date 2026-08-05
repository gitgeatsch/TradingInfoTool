"""Sind die SHORT-Empfehlungen etwas wert - und was kostet der Ausfuehrungshinweis?

DIE ARCHITEKTURFRAGE DAHINTER. Der Nutzer fragte, warum das LLM die
Richtungs-Beschraenkung ueberhaupt sehen muss - SHORT solle gleichwertig
bewertet werden, und der Nur-Long-Schalter nur GUI und Mailversand steuern.
Die Doku zeigt, dass der Schalter urspruenglich etwas ganz anderes war
(Regelwerksmanual, 15.07.): "jede SHORT-Analyse war faktisch verschwendetes
LLM-Budget ... filtert SHORT-Kandidaten schon VOR dem LLM-Aufruf heraus -
keine nachtraegliche Anzeige-Filterung."

Diese Begruendung traegt heute nicht mehr, und zwar messbar: der Vorfilter
wirkt auf `trigger.richtung` VOR dem Aufruf, der Veto von c8dd982 (28.07.)
aber DANACH - er spart kein Budget, die Analyse ist bezahlt und wird
weggeworfen. Und der Vorfilter schuetzt nicht mehr, weil das Modell die
Richtung frei waehlt: 119 dokumentierte Faelle, in denen der Allocator LONG
anfragt und SHORT zurueckkommt.

DAMIT IST DIE ENTSCHEIDENDE FRAGE NICHT "Veto oder Anzeigefilter", sondern ob
die SHORT-Empfehlungen ueberhaupt etwas taugen. Die Betriebsdaten sagen dazu
Widerspruechliches:

    SHORT bis 30.07. (n=80)    Trefferquote 36,6 %   EW +0,502 R   MFE-Med 2,56 R
    SHORT ab  31.07. (n=300)   Trefferquote  9,1 %   EW -1,138 R   MFE-Med 0,60 R

Vor dem Modell-Drift war SHORT die BESTE Gruppe im System, danach die
schlechteste. Beide Zahlen stammen aber aus dem Betrieb und damit von zwei
verschiedenen Modellzustaenden. Was HEUTE gilt, sagt nur ein Test mit dem
heutigen Modell.

WAS HIER GEMESSEN WIRD, beides wie vom Nutzer verlangt:

  RICHTUNG       welcher Anteil der Empfehlungen ist LONG bzw. SHORT
  ZONENQUALITAET das R-Multiple der vom Modell SELBST gesetzten Zonen gegen
                 den tatsaechlichen weiteren Kursverlauf, GETRENNT nach
                 Richtung - bewerte() aus backtest_llm1_historisch

DREI ARME:
    A1  Prompt Stand heute (Regel 2: Richtungen gleichwertig)
    A2  identisch zu A1 - Rauschboden
    B   Regel 2 mit umgekehrtem Ausfuehrungshinweis (SHORT nicht handelbar)

Arm B beantwortet die Zusatzfrage, ob ein Hinweis die Richtung dreht - UND ob
die dadurch entstehenden LONG-Empfehlungen schlechter sind. Genau das ist die
stehende Vorgabe des Nutzers: mehr Signale sollen durch QUALITAET entstehen,
nicht durch Lockerung. Kippt Arm B die Richtung, ohne dass die Zonen halten,
waere nichts gewonnen.

HORIZONT. bewerte() nutzt normalerweise 14 Tage. Die Faktensaetze stammen vom
26.-30.07., die Kursreihe endet am 04./05.08. - es stehen also nur 5-9 Tage
Vorlauf zur Verfuegung. Der Horizont wird deshalb auf 5 Tage gesetzt, was
ohnehin dem vereinbarten Rahmen "0 bis max. 5 Tage" entspricht. Wichtig: das
gilt fuer ALLE Arme gleich, der VERGLEICH bleibt also fair - nur der absolute
R-Wert ist mit diesem kurzen Fenster nicht mit Produktionszahlen vergleichbar.

Lauf: python -u teste_richtung_und_zonen.py [--n 14] [--w 3]
"""
from __future__ import annotations

import io
import json
import os
import re
import statistics
from collections import Counter, defaultdict

import backtest_llm1_historisch as bt
from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import _arg, bewerte, frage, lade_reihen
from datiere_einbruch import ORDNER

# Der Satz aus Regel 2, der dem Modell sagt, es solle die Beschraenkung
# ignorieren. Anfang und Ende, damit eine spaetere Umformulierung auffaellt
# statt still ins Leere zu greifen.
HINWEIS_ANFANG = "Dass Short aktuell nicht über Bitpanda ausführbar ist"
HINWEIS_ENDE = "schlage SHORT vor, wenn die Fakten dafür sprechen."
HINWEIS_UMGEKEHRT = (
    "Short ist über Bitpanda NICHT ausführbar - eine SHORT-Empfehlung kann "
    "nicht gehandelt werden und verfällt. Bewerte die Fakten weiterhin "
    "ehrlich: sprechen sie klar für Short, dann sag das und empfiehl HALTEN "
    "statt eine Long-Position zu konstruieren, die die Daten nicht hergeben."
)
HORIZONT_TAGE = 5


def baue_arme() -> dict[str, str]:
    i = SYSTEM_PROMPT.find(HINWEIS_ANFANG)
    j = SYSTEM_PROMPT.find(HINWEIS_ENDE)
    if i < 0 or j < 0:
        raise SystemExit("Regel-2-Hinweis nicht gefunden - Formulierung geaendert?")
    j += len(HINWEIS_ENDE)
    ersetzt = SYSTEM_PROMPT[:i] + HINWEIS_UMGEKEHRT + SYSTEM_PROMPT[j:]
    if ersetzt == SYSTEM_PROMPT or HINWEIS_ANFANG in ersetzt:
        raise SystemExit("Ersetzung hat nicht gegriffen")
    print(f"  Ersetzt: {j - i} Zeichen -> {len(HINWEIS_UMGEKEHRT)} Zeichen")
    return {"A1 Stand heute": SYSTEM_PROMPT,
            "A2 Stand heute (Rauschen)": SYSTEM_PROMPT,
            "B Short als nicht handelbar": ersetzt}


def lade_faelle(n: int):
    """Echte Faktensaetze mit AUSREICHENDEM Kursvorlauf zum Bewerten.

    Anders als beim Regel-28-Test wird hier NICHT auf HALTEN gefiltert - die
    Frage ist ja gerade, welche Richtung das Modell waehlt und wie gut die
    Zonen sind. Ausgeschlossen bleibt nur der Ungueltig-Pfad."""
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    block = d.get("hebel_faktensaetze") or {}
    if block.get("fehler"):
        raise SystemExit(f"Faktensatz-Block fehlerhaft: {block['fehler']}")
    sig = {s["id"]: s for s in d["hebel_signals"]}
    reihen = lade_reihen()
    kand, verworfen = [], Counter()
    for e in block.get("eintraege", []):
        grund = str(sig.get(e["id"], {}).get("gate_reason") or "")
        if "ltig" in grund and "ung" in grund.lower():
            verworfen["Agent-Antwort ungueltig"] += 1
            continue
        reihe = reihen.get(e["symbol"])
        if not reihe:
            verworfen["keine Kursreihe"] += 1
            continue
        tag = e["created_at"][:10]
        idx = next((k for k, kerze in enumerate(reihe) if kerze.date == tag), None)
        if idx is None:
            verworfen["Tag nicht in der Reihe"] += 1
            continue
        if len(reihe) - idx - 1 < HORIZONT_TAGE:
            verworfen["zu wenig Vorlauf zum Bewerten"] += 1
            continue
        kand.append({**e, "_reihe": reihe, "_idx": idx})
    print(f"  verwendbar: {len(kand)}   verworfen: {dict(verworfen)}")
    kand.sort(key=lambda e: (e["created_at"], e["symbol"]))
    return kand[:: max(1, len(kand) // n)][:n]


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    # bewerte() liest den Horizont aus dem Modul - hier bewusst verkuerzt,
    # weil die Kursreihe nur 5-9 Tage ueber die Faktensaetze hinausreicht.
    bt.HORIZONT = HORIZONT_TAGE

    print("=" * 78)
    print("Arme")
    print("=" * 78)
    arme = baue_arme()
    n, w = _arg("--n", 14), _arg("--w", 3)

    print("\n" + "=" * 78)
    print("Testfaelle")
    print("=" * 78)
    faelle = lade_faelle(n)
    if not faelle:
        print("keine Testfaelle")
        return 1
    print(f"  gezogen {len(faelle)}, Symbole {sorted({f['symbol'] for f in faelle})}")
    print(f"  {len(faelle)} x {len(arme)} x {w} = {len(faelle) * len(arme) * w} Aufrufe")
    print(f"  Bewertungsfenster {HORIZONT_TAGE} Tage")

    client = MistralClient(api_key=key)
    richtung: dict[str, list[str]] = defaultdict(list)
    aktion: dict[str, list[str]] = defaultdict(list)
    r_je_richtung: dict[tuple, list[float]] = defaultdict(list)
    r_je_arm: dict[str, list[float]] = defaultdict(list)
    antworten: list[dict] = []

    for f in faelle:
        fakten = json.loads(f["facts_json"])
        print(f"\n{f['symbol']} @ {f['created_at'][:16]} "
              f"(Betrieb: {f['action']} {f['richtung']}):", flush=True)
        for name, prompt in arme.items():
            zeile = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                akt = str(a.get("action", "?")).upper()
                ric = str(a.get("richtung", "?")).upper()
                aktion[name].append(akt)
                antworten.append({"arm": name, "symbol": f["symbol"],
                                  "created_at": f["created_at"], "antwort": a})
                r = bewerte(a, f["_reihe"], f["_idx"])
                if akt in ("ERÖFFNEN", "EROEFFNEN"):
                    richtung[name].append(ric)
                    if r is not None:
                        r_je_richtung[(name, ric)].append(r)
                        r_je_arm[name].append(r)
                zeile.append(f"{ric[:1]}{'/' + format(r, '.2f') if r is not None else ''}"
                             if akt in ("ERÖFFNEN", "EROEFFNEN") else "HALTEN")
            print(f"  {name:30s} {zeile}", flush=True)

    try:
        ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "richtung_zonen_antworten.json")
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        io.open(ziel, "w", encoding="utf-8").write(json.dumps(antworten, ensure_ascii=False))
        print(f"\n  {len(antworten)} Antworten gesichert: {ziel}")
    except OSError as exc:
        print(f"\n  Antworten NICHT gesichert ({exc})")

    print("\n" + "=" * 78)
    print("1. RICHTUNG - dreht der Ausfuehrungshinweis die Empfehlung?")
    print("=" * 78)
    print(f"{'Arm':30s}{'EROEFFNEN':>11s}{'LONG':>8s}{'SHORT':>8s}")
    for name in arme:
        a = aktion.get(name, [])
        r = richtung.get(name, [])
        if not a:
            continue
        er = sum(1 for x in a if x in ("ERÖFFNEN", "EROEFFNEN")) / len(a)
        lo = sum(1 for x in r if x == "LONG") / len(r) if r else float("nan")
        print(f"{name:30s}{er * 100:10.0f}%{lo * 100:7.0f}%{(1 - lo) * 100:7.0f}%")

    print("\n" + "=" * 78)
    print("2. ZONENQUALITAET - R-Multiple gegen den echten Verlauf, je Richtung")
    print("=" * 78)
    print(f"{'Arm':30s}{'Richtung':>9s}{'n':>5s}{'EW R':>9s}{'Median R':>10s}{'Anteil>0':>10s}")
    for name in arme:
        for ric in ("LONG", "SHORT"):
            v = r_je_richtung.get((name, ric), [])
            if not v:
                continue
            print(f"{name:30s}{ric:>9s}{len(v):5d}{statistics.fmean(v):9.3f}"
                  f"{statistics.median(v):10.3f}"
                  f"{sum(1 for x in v if x > 0) / len(v) * 100:9.0f}%")

    print("\n" + "=" * 78)
    print("3. ZUSAMMEN - taugt die Richtung, die das Modell waehlt?")
    print("=" * 78)
    alle_long = [x for (nm, ric), v in r_je_richtung.items() if ric == "LONG" for x in v]
    alle_short = [x for (nm, ric), v in r_je_richtung.items() if ric == "SHORT" for x in v]
    for lab, v in (("LONG gesamt", alle_long), ("SHORT gesamt", alle_short)):
        if v:
            print(f"  {lab:14s} n={len(v):4d}  EW {statistics.fmean(v):+6.3f} R  "
                  f"Median {statistics.median(v):+6.3f} R  "
                  f"Anteil>0 {sum(1 for x in v if x > 0) / len(v) * 100:.0f}%")
    if alle_long and alle_short and len(alle_long) > 2 and len(alle_short) > 2:
        d = statistics.fmean(alle_long) - statistics.fmean(alle_short)
        se = (statistics.pstdev(alle_long) ** 2 / len(alle_long)
              + statistics.pstdev(alle_short) ** 2 / len(alle_short)) ** 0.5
        print(f"\n  Differenz LONG minus SHORT: {d:+.3f} R  SE {se:.3f}  "
              f"t {(d / se if se else 0):+.2f}")
        print("  " + ("LONG ist besser - der Veto schuetzt, kein Kapazitaetsverlust"
                      if d > 1.96 * se else
                      "SHORT ist besser - der Veto kostet echte Kante"
                      if d < -1.96 * se else
                      "nicht unterscheidbar - die Richtung traegt hier nichts"))
    print("\n  A1 gegen A2 ist der Rauschboden: was zwischen den beiden liegt,")
    print("  ist Wiederholungsvarianz und keine Wirkung von Arm B.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
