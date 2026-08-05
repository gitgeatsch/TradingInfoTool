"""Regel 28 gegen ihren eigenen Elterncommit - ohne jede Rekonstruktion (05.08.).

WARUM EIN ZWEITER ANLAUF. Der erste Aufbau (teste_regel28.py) verglich den
HEUTIGEN Prompt gegen denselben Prompt minus Regel 28. Das ist nicht der
Juli-Zustand: der echte Prompt vom 30.07. hat 28313 Zeichen, meine
Rekonstruktion 30558 - rund 2200 Zeichen an Regeln, die erst NACH dem 30.07.
dazukamen (u.a. die TP-ATR-Leitplanke vom 31.07. 16:14). Der Arm hiess "ohne
Regel 28", trug aber Aenderungen, die es damals noch nicht gab.

Rekonstruktion ist hier auch voellig unnoetig: 350918a und sein Elternteil
4a5095b unterscheiden sich - nachgerechnet, nicht angenommen - durch GENAU
EINEN Einschub von 1085 Zeichen, und das ist Regel 28:

    gemeinsamer Anfang   26487 Zeichen
    Einschub              1085 Zeichen   <- Regel 28
    gemeinsames Ende      1826 Zeichen
    sonst identisch       ja

Damit ist der Vergleich exakt kontrolliert. pruefe_prompts() rechnet das bei
jedem Lauf neu nach, statt es zu glauben.

WAS VOR DEM MODELL GEPRUEFT WURDE. Ein "der Anbieter hat das Modell hinter
demselben Namen getauscht" ist von hier aus nicht widerlegbar und darf deshalb
erst ganz am Ende stehen. Vorher abgeglichen, alles identisch zur Produktion
(agent/krypto/hebel_analyst.py::call_llm_for_hebel_signal):

    Modell            mistral-small-2506 (DEFAULT_MODEL, beide Seiten)
    Temperatur        0.2
    response_format   {"type": "json_object"}
    Nachrichten       system=Prompt, user=json.dumps(facts, ensure_ascii=False)
    Validierung       _validate_hebel() normalisiert nur die Gross-/Klein-
                      schreibung der action und wirft bei Schemafehlern - sie
                      kann EROEFFNEN nie in HALTEN drehen

AUSGESCHLOSSENE FALLGRUPPEN. Drei Pipeline-Pfade setzen HALTEN, ohne dass das
Modell es gewaehlt haette. Zwei speichern keinen Faktensatz und fallen damit
ohnehin heraus; der dritte (AnalystResponseInvalid, gate_reason "Agent-Antwort
ungueltig") speichert facts_json MIT - er wird hier explizit ausgeschlossen,
weil das Modell dort moeglicherweise EROEFFNEN sagte, nur formal falsch.

WARUM NICHT original_action ZUM FILTERN. Das Feld kam erst mit b9a464b am
31.07. 07:01 - vor diesem Datum ist es bei JEDEM Signal leer, egal was das
Modell entschied. Gefiltert wird deshalb ueber risk_veto_reason, das seit dem
14.07. befuellt ist.

DIE GUELTIGKEITSPRUEFUNG BLEIBT DER KERN: alle Faelle haben im Betrieb unter
GENAU dem Prompt von 4a5095b ein HALTEN erzeugt. Reproduziert dieser Arm das
nicht, ist der Aufbau ungueltig - und dann ist genau das der Befund, weil
Prompt, Fakten und Aufrufparameter dann alle nachweislich gleich sind.

Lauf: python -u teste_regel28_echt.py [--n 12] [--w 3]
"""
from __future__ import annotations

import io
import json
import os
import re
import statistics
import subprocess
from collections import Counter, defaultdict

from api.mistral import MistralClient
from backtest_llm1_historisch import _arg, frage
from datiere_einbruch import ORDNER

VOR = "4a5095b"      # 30.07. 18:14 - Elternteil von 350918a
NACH = "350918a"     # 31.07. 06:39 - fuegt Regel 28 ein


def prompt_aus_commit(commit: str) -> str:
    """SYSTEM_PROMPT aus einer historischen Fassung, ohne das Modul zu laden.

    Das Modul zu importieren waere falsch: es zieht Abhaengigkeiten des
    damaligen Standes nach, die heute anders aussehen. Hier wird nur die
    Konstante ausgewertet."""
    quelle = subprocess.run(
        ["git", "show", f"{commit}:agent/krypto/hebel_analyst.py"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    m = re.search(r"^SYSTEM_PROMPT\s*=\s*(.*?)(?=\n[A-Z_]+\s*=|\nclass |\ndef )",
                  quelle, re.S | re.M)
    if not m:
        raise SystemExit(f"SYSTEM_PROMPT in {commit} nicht gefunden")
    return eval(compile(m.group(1), f"<{commit}>", "eval"))


def pruefe_prompts(vor: str, nach: str) -> None:
    """Nachrechnen statt glauben: unterscheiden sich die beiden Fassungen
    wirklich nur durch einen einzigen Einschub, und ist das Regel 28?"""
    i = 0
    while i < min(len(vor), len(nach)) and vor[i] == nach[i]:
        i += 1
    j = 0
    while j < min(len(vor), len(nach)) - i and vor[len(vor) - 1 - j] == nach[len(nach) - 1 - j]:
        j += 1
    einschub = nach[i:len(nach) - j]
    print(f"  Prompt {VOR}: {len(vor)} Zeichen")
    print(f"  Prompt {NACH}: {len(nach)} Zeichen")
    print(f"  gemeinsamer Anfang {i}, gemeinsames Ende {j}, Einschub {len(einschub)}")
    if len(vor) != i + j:
        raise SystemExit("Die Fassungen unterscheiden sich an MEHR als einer Stelle - "
                         "der Vergleich waere nicht kontrolliert.")
    if not einschub.lstrip().startswith("28."):
        raise SystemExit(f"Einschub ist nicht Regel 28: {einschub[:60]!r}")
    print(f"  -> genau ein Einschub, und es ist Regel 28: {einschub.lstrip()[:52]!r}")


def lade_faelle(n: int):
    """Selbst gewaehltes HALTEN von VOR dem 31.07. - ohne Gate-Veto und ohne
    den Ungueltig-Pfad."""
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    block = d.get("hebel_faktensaetze") or {}
    if block.get("fehler"):
        raise SystemExit(f"Faktensatz-Block fehlerhaft: {block['fehler']}")
    sig = {s["id"]: s for s in d["hebel_signals"]}
    kand = []
    verworfen = Counter()
    for e in block.get("eintraege", []):
        s = sig.get(e["id"], {})
        grund = str(s.get("gate_reason") or "")
        if e["created_at"][:10] >= "2026-07-31":
            verworfen["nach dem 31.07."] += 1
        elif str(e.get("action")) != "HALTEN":
            verworfen["kein HALTEN"] += 1
        elif e.get("risk_veto_reason") or s.get("risk_veto"):
            verworfen["vom Gate vetoed"] += 1
        elif "ltig" in grund and "ung" in grund.lower():
            verworfen["Agent-Antwort ungueltig"] += 1
        else:
            kand.append(e)
    kand.sort(key=lambda e: (e["created_at"], e["symbol"]))
    print(f"  verwendbar: {len(kand)}   verworfen: {dict(verworfen)}")
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

    print("=" * 78)
    print("Prompts aus der Historie - unterscheiden sie sich nur durch Regel 28?")
    print("=" * 78)
    p_vor, p_nach = prompt_aus_commit(VOR), prompt_aus_commit(NACH)
    pruefe_prompts(p_vor, p_nach)

    print("\n" + "=" * 78)
    print("Testfaelle")
    print("=" * 78)
    n, w = _arg("--n", 12), _arg("--w", 3)
    faelle = lade_faelle(n)
    if not faelle:
        print("keine Testfaelle")
        return 1

    arme = {
        f"A1 {VOR} (vor R28)": p_vor,
        f"A2 {VOR} (Rauschen)": p_vor,
        f"B  {NACH} (mit R28)": p_nach,
    }
    print(f"  gezogen {len(faelle)}, Symbole {sorted({f['symbol'] for f in faelle})}")
    print(f"  {len(faelle)} x {len(arme)} x {w} = {len(faelle) * len(arme) * w} Aufrufe")

    client = MistralClient(api_key=key)
    akt: dict[str, list[str]] = defaultdict(list)
    konf: dict[str, list[float]] = defaultdict(list)
    je_fall: dict[tuple, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    antworten: list[dict] = []

    for f in faelle:
        fakten = json.loads(f["facts_json"])
        print(f"\n{f['symbol']} @ {f['created_at'][:16]} "
              f"(Betrieb: HALTEN, conf={f['confidence_pct']}):", flush=True)
        for name, prompt in arme.items():
            acts = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                acts.append(str(a.get("action", "?")).upper())
                akt[name].append(acts[-1])
                je_fall[(f["symbol"], f["created_at"])][name].append(acts[-1])
                k = a.get("confidence_pct")
                if isinstance(k, (int, float)):
                    konf[name].append(float(k))
                antworten.append({"arm": name, "symbol": f["symbol"],
                                  "created_at": f["created_at"], "antwort": a})
            print(f"  {name:26s} {dict(Counter(acts))}", flush=True)

    try:
        ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "regel28_echt_antworten.json")
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        io.open(ziel, "w", encoding="utf-8").write(json.dumps(antworten, ensure_ascii=False))
        print(f"\n  {len(antworten)} Antworten gesichert: {ziel}")
    except OSError as exc:
        print(f"\n  Antworten NICHT gesichert ({exc}) - der Lauf zaehlt trotzdem")

    def quote(v, wert):
        return sum(1 for x in v if x == wert) / len(v) if v else float("nan")

    print("\n" + "=" * 78)
    print(f"{'Arm':26s}{'n':>5s}{'HALTEN':>9s}{'EROEFFNEN':>11s}{'Konfidenz':>11s}")
    print("=" * 78)
    for name in arme:
        v = akt.get(name, [])
        if not v:
            continue
        er = sum(1 for x in v if x in ("ERÖFFNEN", "EROEFFNEN")) / len(v)
        print(f"{name:26s}{len(v):5d}{quote(v, 'HALTEN') * 100:8.0f}%{er * 100:10.0f}%"
              f"{(statistics.fmean(konf[name]) if konf.get(name) else float('nan')):10.1f}%")

    print("\n" + "=" * 78)
    print("GUELTIGKEITSPRUEFUNG")
    print("=" * 78)
    a1 = akt.get(f"A1 {VOR} (vor R28)", []) + akt.get(f"A2 {VOR} (Rauschen)", [])
    if not a1:
        print("  Kontrollarme leer")
        return 1
    halten = quote(a1, "HALTEN")
    print(f"  Der Prompt von {VOR} haelt heute in {halten * 100:.0f}% der Faelle.")
    print("  Im Betrieb hielt er bei GENAU DIESEN Faktensaetzen zu 100%.")
    if halten < 0.5:
        print("\n  AUFBAU REPRODUZIERT DIE PRODUKTION NICHT - und das ist diesmal")
        print("  selbst der Befund: Prompt (bitgleich aus git), Fakten (bitgleich")
        print("  aus facts_json), Modellname, Temperatur und response_format sind")
        print("  nachweislich identisch zur Produktion. Bleibt die Antwort")
        print("  trotzdem anders, liegt der Unterschied NICHT in unserem Code.")
        print("  Regel 28 ist damit als Ursache ENTLASTET - sie kann einen")
        print("  Umschwung nicht erklaeren, der schon ohne sie eintritt.")
        return 0
    print("  -> Aufbau gueltig.")

    print("\n" + "=" * 78)
    print("WIRKUNG von Regel 28, gepaart je Faktensatz")
    print("=" * 78)
    d = []
    for fid, arme_werte in je_fall.items():
        basis = arme_werte.get(f"A1 {VOR} (vor R28)", []) + arme_werte.get(f"A2 {VOR} (Rauschen)", [])
        mit = arme_werte.get(f"B  {NACH} (mit R28)", [])
        if basis and mit:
            def er(v):
                return sum(1 for x in v if x in ("ERÖFFNEN", "EROEFFNEN")) / len(v)
            d.append(er(mit) - er(basis))
    if len(d) < 3:
        print("  zu wenige gepaarte Faelle")
        return 0
    mw, sd = statistics.fmean(d), statistics.stdev(d)
    se = sd / (len(d) ** 0.5)
    print(f"  EROEFFNEN-Differenz (mit R28 minus ohne): {mw:+.3f}")
    print(f"  SE {se:.3f}  t {(mw / se if se else 0):+.2f}  n {len(d)} Faktensaetze")
    print("  " + ("REGEL 28 TRAEGT den Umschwung" if abs(mw) > 1.96 * se
                  else "nicht von Rauschen unterscheidbar"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
