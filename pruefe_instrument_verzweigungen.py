# -*- coding: utf-8 -*-
"""Jede Verzweigung am `instrument` in der NEUEN Kette - mit Urteil.

⚠️ WOZU. S6b hat den zweiten Lauf entfernt: Krypto laeuft seither NUR mit
`instrument="spot"`. Jede Bedingung der Form `instrument == "hebel"` ist damit
fuer Krypto TOTER CODE - und keine davon wird rot, sie tut einfach nichts mehr.

GEFUNDEN WURDEN SO, EINZELN UND ZU SPAET:

    23.08.  der Cooldown-Topf des Hebel-Laufs (3,5 h) - Produktion stumm
    23.08.  Finanzierungsrate und Liquidationsabstand im Lagebild
    23.08.  ⚠️ `rechne()` rechnet den Hebel aus dem LAUF - seit S6b nie mehr
    23.08.  ⚠️ die `hebel`-Spalte wird nie geschrieben - Topf und Cooldown tot

DIESES WERKZEUG LISTET SIE ALLE, mit ihrem Urteil. Wer eine neue Verzweigung
am Instrument baut, muss sie hier eintragen - sonst faellt die Pruefung durch.
"""
from __future__ import annotations

import ast
import io
import subprocess
import sys

sys.path.insert(0, ".")

# Die Module der NEUEN Kette. Die alten Pipelines duerfen am Instrument
# verzweigen - dort gibt es beide Laeufe noch.
NEUE_KETTE = {
    "rollen_lauf", "rollen_eingabe", "rollen_gate", "rolle_trader",
    "rolle_analyst", "gegenpruefer_rollen", "empfehlung_vertrag",
    "entscheidungsrechnung", "betraege", "toepfe", "assetklassen",
    "lagebeschreibung", "positionierung", "handelsauftrag", "warteschlange",
    "wiederholung", "anlass", "anlass_kalender", "signal_abbildung",
    "signal_mail", "vorfilter", "wahrscheinlichkeit", "asset_schalter",
    "szenario_fakten", "faktenblock", "verkaufsrechnung", "ausstiegsrechnung",
    "marktlage", "mindestkriterien", "llm_schema",
}

# ⚠️ JEDE STELLE TRAEGT IHR URTEIL, keinen Haken. `lebt` heisst: sie bekommt
# das ERGEBNIS-Etikett und kann weiterhin "hebel" sehen. `tot` heisst: sie
# bekommt das LAUF-Etikett und ist fuer Krypto seit S6b wirkungslos.
URTEIL = {
    ("entscheidungsrechnung.py", "_crv_faktor"): (
        "tot", "bekommt das Lauf-Etikett aus `rechne()` - die CRV-Abstufung "
               "unterscheidet Spot und Hebel seit S6b nicht mehr"),
    ("entscheidungsrechnung.py", "rechne"): (
        "tot", "⚠️ DER GROSSE: `rechne()` rechnet den Hebel aus dem LAUF. "
               "Seit S6b immer 'spot', also IMMER Hebel 1,0. "
               "`dimensioniere()` wurde umgestellt, `rechne()` nicht - und "
               "die Produktion ruft `rechne()`"),
    ("entscheidungsrechnung.py", "saetze"): (
        "lebt", "liest `e['instrument']` aus der fertigen Rechnung"),
    ("lagebeschreibung.py", "_bestand"): (
        "tot", "der Bestandssatz unterscheidet Spot- und Hebelposition - "
               "harmlos, weil `rollen_lauf` seit S6b BEIDE Bestaende liest"),
    ("positionierung.py", "_melde"): (
        "tot", "unterdrueckte die Luecken-Meldung im Hebel-Lauf; der "
               "Spot-Lauf meldete sie schon immer - unveraendert"),
    ("rollen_eingabe.py", "baue_fall"): (
        "tot", "waehlt die Gegenbestands-Richtung - harmlos, der spot-Zweig "
               "nennt die Hebelposition"),
    ("rollen_eingabe.py", "bestand"): (
        "tot", "las im Hebel-Lauf die Hebelposition. Harmlos, weil "
               "`rollen_lauf` seit S6b BEIDE Bestaende liest und die "
               "Hebelposition Vorrang hat"),
    ("rollen_eingabe.py", "gegenbestand_satz"): (
        "tot", "der Satz 'daneben liegt auch ...' - der spot-Zweig nennt die "
               "Hebelposition, also unveraendert richtig"),
    ("signal_abbildung.py", "felder_aus_entscheidung"): (
        "tot", "⚠️ ENTSCHEIDET UEBER DIE `hebel`-SPALTE. Seit S6b nie "
               "gefuellt - `toepfe.sql_bedingung()` trennt die Toepfe an "
               "genau dieser Spalte, und der Hebel-Cooldown haengt daran"),
    ("signal_mail.py", "baue_mail"): (
        "tot", "Betreff und Abschnitt der Mail - kosmetisch, aber falsch, "
               "solange die Rechnung einen Hebel ergeben kann"),
    ("toepfe.py", "sql_bedingung"): (
        "lebt", "bekommt `_topf_instrument`, also das ERGEBNIS"),
    ("toepfe.py", "budget_eur"): (
        "lebt", "bekommt `_topf_instrument`, also das ERGEBNIS"),
    ("warteschlange.py", "_bestaende"): (
        "tot", "Reihenfolge des Bestands - harmlos, beide Zweige liefern "
               "dieselben zwei Groessen, nur vertauscht"),
    ("warteschlange.py", "erklaere"): (
        "tot", "nur Text zur Reihenfolge"),
}


class Sammler(ast.NodeVisitor):
    def __init__(self) -> None:
        self.funde: list[tuple[int, str]] = []

    def _pruefe(self, knoten) -> None:
        text = ast.unparse(knoten)
        if "instrument" not in text or len(text) > 90:
            return
        if any(w in text for w in ('"hebel"', "'hebel'", '"spot"', "'spot'")):
            self.funde.append((knoten.lineno, text[:80]))

    def visit_Compare(self, knoten):
        self._pruefe(knoten)
        self.generic_visit(knoten)

    def visit_Subscript(self, knoten):
        if "instrument" in ast.unparse(knoten):
            self.funde.append((knoten.lineno, ast.unparse(knoten)[:80]))
        self.generic_visit(knoten)


def _funktion_bei(quelle: str, zeile: int) -> str:
    name = "?"
    for i, l in enumerate(quelle.split("\n"), 1):
        if i > zeile:
            break
        s = l.strip()
        if s.startswith("def "):
            name = s[4:].split("(")[0]
    return name


def pruefe() -> int:
    dateien = [f for f in subprocess.run(
        ["git", "ls-files", "agent/*.py"], capture_output=True, text=True,
        encoding="utf-8").stdout.split()
        if f.replace("agent/", "").replace(".py", "") in NEUE_KETTE]
    gesehen, offen = set(), []
    print(f"{'Datei':26}{'Funktion':26}{'Urteil':8}Zeilen")
    print("=" * 92)
    for pfad in sorted(dateien):
        try:
            quelle = io.open(pfad, encoding="utf-8").read()
            baum = ast.parse(quelle)
        except (OSError, SyntaxError):
            continue
        s = Sammler()
        s.visit(baum)
        je_funktion: dict[str, list[int]] = {}
        for ln, _ in sorted(set(s.funde)):
            je_funktion.setdefault(_funktion_bei(quelle, ln), []).append(ln)
        kurz = pfad.replace("agent/", "")
        for fn, zeilen in sorted(je_funktion.items()):
            gesehen.add((kurz, fn))
            urteil, grund = URTEIL.get((kurz, fn), ("OFFEN", ""))
            if urteil == "OFFEN":
                offen.append(f"{kurz}::{fn} (Zeile {zeilen[0]})")
            print(f"  {kurz:24}{fn:26}{urteil:8}"
                  f"{', '.join(str(z) for z in zeilen)}")
    print("=" * 92)
    verwaist = [f"{d}::{f}" for d, f in URTEIL if (d, f) not in gesehen]
    for zeile in offen:
        print(f"  FEHL  ohne Urteil: {zeile}")
    for zeile in verwaist:
        print(f"  FEHL  Urteil ohne Fundstelle: {zeile}")
    tot = sum(1 for u, _ in URTEIL.values() if u == "tot")
    print(f"\n{len(gesehen)} Stellen, {tot} davon fuer Krypto TOT seit S6b")
    if not offen and not verwaist:
        print("  OK    jede Stelle traegt ihr Urteil")
    return 1 if (offen or verwaist) else 0


if __name__ == "__main__":
    raise SystemExit(pruefe())
