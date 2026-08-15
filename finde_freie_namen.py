# -*- coding: utf-8 -*-
"""Welche Funktion greift auf einen Namen zu, den sie nicht kennt?

DREIMAL DIESELBE FALLE an zwei Tagen: `VK` (14.08.), `_wl` und `assetklasse`
(15.08.). Jedes Mal eine Variable aus `fuehre_lauf` oder `_ein_asset`, benutzt
in einer Funktion, die sie nicht sieht - und jedes Mal vom breiten Fehlerfang
geschluckt.

    Der Fehler faellt erst im BETRIEB auf, und nur, wenn jemand die Daten
    nachzaehlt. `assetklasse` hat zwei Vormittage lang jede einzelne
    Nein-Zeile verhindert, ohne eine Logzeile.

DIESE PRUEFUNG BRAUCHT KEIN AUSFUEHREN. Sie liest den Syntaxbaum: fuer jede
Funktion auf Modulebene die benutzten Namen gegen die bekannten (Parameter,
lokale Zuweisungen, Modulebene, Builtins, Importe). Was uebrig bleibt, ist ein
Kandidat.
"""
from __future__ import annotations

import ast
import builtins
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W = r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool"


class _Sammler(ast.NodeVisitor):
    """Namen, die in einer Funktion GEBUNDEN werden."""

    def __init__(self):
        self.gebunden = set()

    def visit_Name(self, n):
        if isinstance(n.ctx, (ast.Store, ast.Del)):
            self.gebunden.add(n.id)

    def visit_arg(self, n):
        self.gebunden.add(n.arg)

    def visit_alias(self, n):
        self.gebunden.add((n.asname or n.arg if hasattr(n, "arg")
                           else n.asname or n.name).split(".")[0])

    def visit_ExceptHandler(self, n):
        if n.name:
            self.gebunden.add(n.name)
        self.generic_visit(n)

    def visit_FunctionDef(self, n):
        self.gebunden.add(n.name)
        self.generic_visit(n)

    def visit_ClassDef(self, n):
        self.gebunden.add(n.name)
        self.generic_visit(n)

    def visit_comprehension(self, n):
        self.generic_visit(n)


def _namen(fn: ast.AST) -> tuple[set, set]:
    s = _Sammler()
    for k in ast.walk(fn):
        s.visit(k)
    benutzt = {k.id for k in ast.walk(fn)
               if isinstance(k, ast.Name) and isinstance(k.ctx, ast.Load)}
    return s.gebunden, benutzt


def pruefe_datei(pfad: str) -> list[tuple[str, str]]:
    with open(pfad, "r", encoding="utf-8") as f:
        baum = ast.parse(f.read(), filename=pfad)
    # Alles, was auf MODULEBENE bekannt ist.
    modul = set(dir(builtins))
    for k in baum.body:
        if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            modul.add(k.name)
        elif isinstance(k, (ast.Import, ast.ImportFrom)):
            for a in k.names:
                modul.add((a.asname or a.name).split(".")[0])
        elif isinstance(k, ast.Assign):
            for z in k.targets:
                for n in ast.walk(z):
                    if isinstance(n, ast.Name):
                        modul.add(n.id)
        elif isinstance(k, (ast.AnnAssign, ast.AugAssign)):
            for n in ast.walk(k.target):
                if isinstance(n, ast.Name):
                    modul.add(n.id)
        elif isinstance(k, ast.Try):
            for z in ast.walk(k):
                if isinstance(z, (ast.Import, ast.ImportFrom)):
                    for a in z.names:
                        modul.add((a.asname or a.name).split(".")[0])

    treffer = []
    for k in baum.body:
        if not isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        gebunden, benutzt = _namen(k)
        offen = benutzt - gebunden - modul
        for name in sorted(offen):
            treffer.append((k.name, name))
    return treffer


def main() -> int:
    ordner = [os.path.join(W, "agent"), os.path.join(W, "scheduler"),
              os.path.join(W, "database"), os.path.join(W, "ui")]
    gesamt = 0
    for o in ordner:
        for wurzel, _, dateien in os.walk(o):
            for name in sorted(dateien):
                if not name.endswith(".py"):
                    continue
                pfad = os.path.join(wurzel, name)
                try:
                    tr = pruefe_datei(pfad)
                except SyntaxError as exc:
                    print(f"  ! {pfad}: {exc}")
                    continue
                if tr:
                    rel = os.path.relpath(pfad, W)
                    print(f"\n{rel}")
                    for fn, n in tr:
                        print(f"    {fn}() benutzt '{n}'")
                        gesamt += 1
    print(f"\n{'=' * 60}\nKANDIDATEN GESAMT: {gesamt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
