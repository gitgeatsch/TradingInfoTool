"""Verursacht Regel 28 den Umschwung von HALTEN auf EROEFFNEN? (05.08.)

DER BEFUND, DER DAZU FUEHRT. Am 31.07. kippt das Hebel-Verhalten binnen einer
Stunde: vorher rund 50 HALTEN und 4 EROEFFNEN taeglich, danach rund 40
EROEFFNEN und 2 HALTEN, bei 97 % SHORT-Anteil und um zehn Punkte hoeherer
Konfidenz. Der Markt erklaert das nicht - der Indikatorsatz aus der Produktion
zeigt an dem Tag keinen Bruch (bester Trennpunkt 12.07.), und bei UNVERAENDERT
nicht-bearischer Datenlage stieg der SHORT-Anteil von 5,2 % auf 69,9 %.

DER VERDACHT. Regel 28 (350918a, 31.07. 04:39 UTC) ist die EINZIGE
Prompt-Aenderung im Deploy-Fenster vor dem Sprung. Sie verlangt, bei selbst
gewaehltem HALTEN die Zonen auszufuellen, die man bei EROEFFNEN gewaehlt
haette - das Modell muss den Trade-Fall also konkret ausarbeiten, BEVOR es
haelt. Dass ein konkret ausgearbeiteter Fall dann auch gewaehlt wird, ist ein
bekannter Effekt.

Regel 27 kommt als zweiter Arm dazu, weil 350918a selbst die Kopplung nennt:
"Ein selbst gewaehltes HALTEN ohne Gate/Veto - seit Regel 27 der Normalfall".
Regel 27 schuf den Fall, Regel 28 haengt die Trade-Ausarbeitung genau daran.

WARUM DIESER AUFBAU UND NICHT DER HISTORISCHE BACKTEST. Dort liegt die
EROEFFNEN-Quote in ALLEN Armen bei 94-100 %: der rekonstruierte Faktensatz ist
zu duenn, um ueberhaupt ein HALTEN zu erzeugen, und genau die Achse, um die es
geht, ist damit gesaettigt. Hier laufen stattdessen die ECHTEN Faktensaetze aus
`facts_json` - dieselben, die im Betrieb nachweislich HALTEN erzeugt haben.

DIE GUELTIGKEITSPRUEFUNG IST DER KERN DES AUFBAUS, nicht ein Anhang. Alle
Testfaelle sind Faktensaetze von VOR dem 31.07., bei denen das LLM selbst
HALTEN waehlte - unter einem Prompt OHNE Regel 28. Der Arm "ohne R28" muss
dieses HALTEN also reproduzieren. Tut er das nicht, bildet der Aufbau die
Produktion nicht ab und KEIN Ergebnis darunter zaehlt. Ohne diese Klammer
waere ein hoher EROEFFNEN-Anteil im A-Arm nicht von "das Modell eroeffnet hier
eben immer" unterscheidbar - das ist exakt der Fehler, an dem der historische
Backtest scheitert.

VIER ARME:
    A1  Prompt Stand heute (mit Regel 27 UND 28)
    A2  identisch zu A1 - der Abstand A1<->A2 ist der Rauschboden
    B   ohne Regel 28          <- der eigentliche Test
    C   ohne Regel 27 und 28   <- Stand vor dem 29.07.

Lauf: python -u teste_regel28.py [--n 16] [--w 3]
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import _arg, frage
from datiere_einbruch import ORDNER

BLOECKE = {
    "R28": ("28. Reine Daten-Vervollstaendigung", "waere schlechter als gar keine."),
    "R27": ("27. Regelwerk-Audit Stufe 3, Punkt 4", "siehe project_regelwerk_audit_29_07.md)."),
}


def entferne(prompt: str, anfang: str, ende: str) -> str:
    a = prompt.index(anfang)
    b = prompt.index(ende, a) + len(ende)
    while a > 0 and prompt[a - 1] == " ":
        a -= 1
    return prompt[:a] + prompt[b:]


def baue_varianten() -> dict[str, str]:
    """Jede Entfernung wird geprueft: findet ein Anker nicht, waere der Arm in
    Wahrheit mit dem Kontrollarm identisch - und das Ergebnis saehe wie ein
    sauberer Negativbefund aus."""
    for name, (a, e) in BLOECKE.items():
        if SYSTEM_PROMPT.count(a) != 1:
            raise SystemExit(f"Anker {name} nicht eindeutig ({SYSTEM_PROMPT.count(a)}x)")
    ohne28 = entferne(SYSTEM_PROMPT, *BLOECKE["R28"])
    ohne2728 = entferne(ohne28, *BLOECKE["R27"])
    for name, p, mindest in (("ohne R28", ohne28, 900), ("ohne R27+28", ohne2728, 2700)):
        weg = len(SYSTEM_PROMPT) - len(p)
        if weg < mindest:
            raise SystemExit(f"{name}: nur {weg} Zeichen entfernt, erwartet >= {mindest}")
        print(f"  {name:14s} -{weg:5d} Zeichen")
    return {"A1 Stand heute": SYSTEM_PROMPT, "A2 Stand heute (Rauschen)": SYSTEM_PROMPT,
            "B ohne Regel 28": ohne28, "C ohne Regel 27+28": ohne2728}


def lade_testfaelle(n: int):
    """Faktensaetze von VOR dem 31.07., bei denen das LLM SELBST HALTEN
    waehlte - kein Gate-Veto, keine uebersetzte Kontrathese.

    `action` in der Signalzeile ist die Entscheidung NACH dem Gate; die
    urspruengliche steht in `original_action` und ist nur dort gesetzt, wo das
    Gate eingegriffen hat. Ein leeres `original_action` bei action=HALTEN
    heisst also: das Modell hat selbst gehalten."""
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    block = d.get("hebel_faktensaetze") or {}
    if block.get("fehler"):
        raise SystemExit(f"Faktensatz-Block fehlerhaft: {block['fehler']}")
    sig = {s["id"]: s for s in d["hebel_signals"]}
    kand = [e for e in block.get("eintraege", [])
            if e["created_at"][:10] < "2026-07-31"
            and str(e.get("action")) == "HALTEN"
            and not sig.get(e["id"], {}).get("original_action")
            and not e.get("risk_veto_reason")]
    kand.sort(key=lambda e: (e["created_at"], e["symbol"]))
    # gleichmaessig ueber Tage und Symbole ziehen statt der ersten n
    return kand[:: max(1, len(kand) // n)][:n], len(kand)


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

    print("=" * 78)
    print("Blockpruefung")
    print("=" * 78)
    varianten = baue_varianten()

    n, w = _arg("--n", 16), _arg("--w", 3)
    faelle, gesamt = lade_testfaelle(n)
    if not faelle:
        print("keine Testfaelle - Faktensatz-Block leer oder Fenster falsch")
        return 1

    print("\n" + "=" * 78)
    print(f"{len(faelle)} echte Faktensaetze (von {gesamt} verfuegbaren) x "
          f"{len(varianten)} Arme x {w} = {len(faelle) * len(varianten) * w} Aufrufe")
    print(f"Alle aus dem Zeitraum {faelle[0]['created_at'][:10]} .. "
          f"{faelle[-1]['created_at'][:10]}, Symbole: "
          f"{sorted({f['symbol'] for f in faelle})}")
    print("ALLE haben im Betrieb HALTEN erzeugt - unter einem Prompt OHNE Regel 28.")
    print("=" * 78)

    client = MistralClient(api_key=key)
    akt = defaultdict(list)
    konf = defaultdict(list)
    je_fall = defaultdict(lambda: defaultdict(list))

    for f in faelle:
        fakten = json.loads(f["facts_json"])
        print(f"\n{f['symbol']} @ {f['created_at'][:16]} "
              f"(Betrieb: HALTEN, conf={f['confidence_pct']}):", flush=True)
        for name, prompt in varianten.items():
            acts = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                akt_wert = str(a.get("action", "?")).upper()
                acts.append(akt_wert)
                akt[name].append(akt_wert)
                je_fall[(f["symbol"], f["created_at"])][name].append(akt_wert)
                k = a.get("confidence_pct")
                if isinstance(k, (int, float)):
                    konf[name].append(float(k))
            print(f"  {name:28s} {dict(Counter(acts))}", flush=True)

    def eroeffnet(werte):
        return sum(1 for x in werte if x in ("ERÖFFNEN", "EROEFFNEN"))

    print("\n" + "=" * 78)
    print(f"{'Arm':28s}{'n':>5s}{'EROEFFNEN':>11s}{'HALTEN':>9s}{'Konfidenz':>11s}")
    print("=" * 78)
    for name in varianten:
        v = akt.get(name, [])
        if not v:
            continue
        er = eroeffnet(v)
        ha = sum(1 for x in v if x == "HALTEN")
        print(f"{name:28s}{len(v):5d}{er / len(v) * 100:10.0f}%{ha / len(v) * 100:8.0f}%"
              f"{(statistics.fmean(konf[name]) if konf.get(name) else float('nan')):10.1f}%")

    print("\n" + "=" * 78)
    print("GUELTIGKEITSPRUEFUNG - bildet der Aufbau die Produktion ab?")
    print("=" * 78)
    b = akt.get("B ohne Regel 28", [])
    if not b:
        print("  Arm B leer - nicht bewertbar")
        return 1
    b_halten = sum(1 for x in b if x == "HALTEN") / len(b)
    print(f"  Arm B (ohne Regel 28) haelt in {b_halten * 100:.0f}% der Faelle.")
    print("  Im Betrieb hielt das Modell bei GENAU DIESEN Faktensaetzen zu 100%.")
    if b_halten < 0.5:
        print("\n  AUFBAU UNGUELTIG: der Arm ohne Regel 28 reproduziert das")
        print("  HALTEN nicht. Damit ist ein hoher EROEFFNEN-Anteil in A nicht")
        print("  von 'das Modell eroeffnet hier eben immer' unterscheidbar -")
        print("  derselbe Sattigungsfehler wie im historischen Backtest.")
        print("  KEIN Ergebnis unterhalb dieser Zeile zaehlt.")
        return 2
    print("  -> Aufbau gueltig, die Auswertung darunter ist belastbar.")

    print("\n" + "=" * 78)
    print("WIRKUNG - gepaart je Faktensatz, gegen den Rauschboden")
    print("=" * 78)
    faelle_ids = sorted(je_fall)

    def anteil(fid, arm):
        v = je_fall[fid].get(arm, [])
        return eroeffnet(v) / len(v) if v else None

    rausch = []
    for fid in faelle_ids:
        a1 = anteil(fid, "A1 Stand heute")
        a2 = anteil(fid, "A2 Stand heute (Rauschen)")
        if a1 is not None and a2 is not None:
            rausch.append(a1 - a2)
    boden = statistics.stdev(rausch) if len(rausch) > 2 else float("nan")
    print(f"  Rauschboden (Streuung A1 gegen A2, gepaart): {boden:.3f}")
    for arm in ("B ohne Regel 28", "C ohne Regel 27+28"):
        d = []
        for fid in faelle_ids:
            basis = [anteil(fid, "A1 Stand heute"), anteil(fid, "A2 Stand heute (Rauschen)")]
            basis = [x for x in basis if x is not None]
            g = anteil(fid, arm)
            if basis and g is not None:
                d.append(statistics.fmean(basis) - g)
        if len(d) < 3:
            continue
        mw, sd = statistics.fmean(d), statistics.stdev(d)
        se = sd / math.sqrt(len(d))
        urteil = "TRAEGT" if abs(mw) > 1.96 * se else "nicht unterscheidbar"
        print(f"  {arm:24s} EROEFFNEN-Differenz zu A: {mw:+.3f}  "
              f"SE {se:.3f}  t {(mw / se if se else 0):+.2f}  {urteil}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
