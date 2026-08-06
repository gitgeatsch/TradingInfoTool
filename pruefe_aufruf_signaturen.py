"""Findet Aufrufe, die Argumente uebergeben, die die Zielfunktion nicht kennt.

ANLASS (06.08.2026). `hebel_pipeline.py` uebergab `crv_baender=` an
`build_hebel_facts()`, dessen Signatur den Parameter nicht hatte - obwohl der
Funktionsrumpf ihn bereits benutzte und die fuenf anderen Analysten ihn hatten.
Ergebnis: JEDER Hebel-LLM-Call brach mit einem TypeError ab. Python findet so
etwas erst zur Laufzeit, und da faengt es der naechste try/except ab.

Diese Pruefung ist die Antwort auf "vor einem Fix sauber analysieren, damit wir
keinen Dominoeffekt haben": statt einen gemeldeten Fehler zu beheben und auf
den naechsten zu warten, wird die GANZE Klasse auf einmal geprueft.

VERFAHREN. Rein statisch ueber den AST, kein Import, keine Ausfuehrung:
  1. alle Funktions- und Methodendefinitionen im Projekt einsammeln
  2. alle Aufrufe einsammeln, die einen dieser Namen tragen
  3. je Aufruf pruefen, ob jedes Schluesselwort-Argument in der Signatur steht

GRENZEN, die dazugehoeren:
  - Ein Name, der mehrfach mit VERSCHIEDENEN Signaturen definiert ist, kann
    statisch nicht zugeordnet werden. Solche Faelle werden als "mehrdeutig"
    ausgewiesen, nicht als Fehler - sonst erzeugt die Pruefung Rauschen und
    wird nicht mehr gelesen.
  - `**kwargs` in der Signatur macht jeden Schluessel gueltig.
  - Positionsargumente werden nur gezaehlt, nicht auf Typen geprueft.
Die Pruefung findet also die eine Fehlerklasse zuverlaessig, nicht alles.
"""
import ast
import pathlib
import sys
from collections import defaultdict

WURZEL = pathlib.Path(__file__).parent
AUSGENOMMEN = {".venv", "venv", "__pycache__", ".git", "node_modules"}


def dateien():
    for pfad in WURZEL.rglob("*.py"):
        if any(teil in AUSGENOMMEN for teil in pfad.parts):
            continue
        yield pfad


def signatur(knoten: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    a = knoten.args
    namen = {p.arg for p in (a.posonlyargs + a.args + a.kwonlyargs)}
    return {
        "namen": namen,
        "hat_kwargs": a.kwarg is not None,
        "hat_varargs": a.vararg is not None,
        "positional": len(a.posonlyargs) + len(a.args),
        "pflicht_positional": len(a.posonlyargs) + len(a.args) - len(a.defaults),
    }


# --- 1) Definitionen einsammeln -------------------------------------------
definitionen: dict[str, list[tuple[str, dict]]] = defaultdict(list)
baeume: dict[pathlib.Path, ast.Module] = {}
for pfad in dateien():
    try:
        baum = ast.parse(pfad.read_text(encoding="utf-8"), str(pfad))
    except SyntaxError as exc:
        print(f"  SYNTAXFEHLER {pfad.relative_to(WURZEL)}: {exc}")
        continue
    baeume[pfad] = baum
    for knoten in ast.walk(baum):
        if isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitionen[knoten.name].append((str(pfad.relative_to(WURZEL)), signatur(knoten)))

# --- 2) Aufrufe pruefen ---------------------------------------------------
fehler, mehrdeutig = [], []
for pfad, baum in baeume.items():
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.Call):
            continue
        ziel = knoten.func
        name = ziel.id if isinstance(ziel, ast.Name) else (
            ziel.attr if isinstance(ziel, ast.Attribute) else None)
        if not name or name not in definitionen:
            continue
        kandidaten = definitionen[name]
        signaturen = {frozenset(s["namen"]) | frozenset(["**"] if s["hat_kwargs"] else [])
                      for _, s in kandidaten}
        uebergeben = {kw.arg for kw in knoten.keywords if kw.arg}
        if len(signaturen) > 1:
            # Nur melden, wenn KEINE der Signaturen passt - dann ist es
            # unabhaengig von der Zuordnung ein Fehler.
            if all(not s["hat_kwargs"] and (uebergeben - s["namen"]) for _, s in kandidaten):
                mehrdeutig.append((pfad, knoten.lineno, name, uebergeben, kandidaten))
            continue
        datei, sig = kandidaten[0]
        if sig["hat_kwargs"]:
            continue
        unbekannt = uebergeben - sig["namen"]
        if unbekannt:
            fehler.append((pfad, knoten.lineno, name, sorted(unbekannt), datei))

# --- 3) Bericht -----------------------------------------------------------
print(f"{len(baeume)} Dateien, {len(definitionen)} Funktionsnamen geprueft\n")
if fehler:
    print(f"FEHLER - Argument existiert in der Signatur nicht ({len(fehler)}):")
    for pfad, zeile, name, unbekannt, definiert_in in fehler:
        print(f"  {pfad.relative_to(WURZEL)}:{zeile}  {name}(...) kennt kein "
              f"{', '.join(unbekannt)}  [definiert in {definiert_in}]")
else:
    print("Keine unbekannten Schluesselwort-Argumente gefunden.")

if mehrdeutig:
    print(f"\nZU PRUEFEN - Name mehrfach definiert, KEINE Signatur passt ({len(mehrdeutig)}):")
    for pfad, zeile, name, uebergeben, kandidaten in mehrdeutig:
        print(f"  {pfad.relative_to(WURZEL)}:{zeile}  {name}({', '.join(sorted(uebergeben))})")
        for datei, _ in kandidaten:
            print(f"      definiert in {datei}")

sys.exit(1 if (fehler or mehrdeutig) else 0)
