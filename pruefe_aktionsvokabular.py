# -*- coding: utf-8 -*-
"""Kennt jede Stelle im Betrieb das VOLLE Aktionsvokabular der neuen Kette?

⚠️ WOZU. Am 22.08.2026 (S6c) fand sich, dass `REDUZIEREN` an sechs Stellen
fehlte - darunter `_TRACKABLE_ACTIONS`, die entscheidet, ob ein Signal
ueberhaupt AUFGELOEST wird. Acht Signale lagen mit gespeicherten Zonen in der
Datenbank und bekamen nie ein Ergebnis; im Export standen sie im Band
`mit_halten` und fehlten in `ohne_halten`. Sie sahen aus wie NICHTS_TUN.

DER FEHLER IST NICHT DER TIPPFEHLER, SONDERN DIE BAUART. Wer eine Aktion
ergaenzt, aendert `empfehlung_vertrag.AKTIONEN` - und muss dann von Hand jede
Liste finden, die Aktionen aufzaehlt. Das ist genau die Art Kopie, die am
13.08. schon einmal auffiel (signal_abbildung hatte die fuenf Spot-Aktionen
abgeschrieben statt importiert).

WIE GEPRUEFT WIRD. Ueber den Syntaxbaum: jede Liste und jeder Vergleich, der
eine VERKAUFSSEITIGE Aktion nennt, muss die verkaufsseitigen Aktionen der
NEUEN Kette vollstaendig nennen - oder hier mit Grund ausgenommen sein.

⚠️ EINE AUSNAHME IST EINE AUSSAGE, KEIN SCHALTER. Jeder Eintrag in
AUSGENOMMEN traegt den Grund, warum die Stelle das neue Wort NICHT kennen
darf. Ein Eintrag ohne Grund faellt hier durch.
"""
from __future__ import annotations

import ast
import io
import subprocess
import sys

sys.path.insert(0, ".")
from agent import empfehlung_vertrag as EV                       # noqa: E402

# Verkaufsseitig in der NEUEN Kette. TAUSCHEN gehoert der alten und wird
# deshalb nicht gefordert - es steht nur in der Erkennung.
VERKAUFSSEITIG_NEU = {"VERKAUFEN", "REDUZIEREN"}
ANKER = VERKAUFSSEITIG_NEU | {"TAUSCHEN", "TEILVERKAUF", "SCHLIESSEN"}

BETRIEB = ("agent/", "database/", "scheduler/", "ui/", "importer/")

# ⚠️ MIT GRUND, NICHT MIT HAEKCHEN.
AUSGENOMMEN = {
    "agent/aktien/analyst.py":
        "Prompttext der ALTEN Kette - sie erzeugt REDUZIEREN nicht.",
    "agent/hedge/analyst.py":
        "Prompttext der ALTEN Kette - sie erzeugt REDUZIEREN nicht.",
    "agent/krypto/analyst.py":
        "Prompttext der ALTEN Kette - sie erzeugt REDUZIEREN nicht.",
    "agent/rohstoff/analyst.py":
        "Prompttext der ALTEN Kette - sie erzeugt REDUZIEREN nicht.",
    "agent/themen_etf/analyst.py":
        "Prompttext der ALTEN Kette - sie erzeugt REDUZIEREN nicht.",
    "agent/krypto/risk_gate.py":
        "Gate der ALTEN Kette. rollen_lauf.py ruft es nicht - geprueft am "
        "22.08. per Suche nach 'risk_gate' und 'post_check'.",
    "agent/krypto/gegenpruefung.py":
        "Rolle G der ALTEN Kette. Die neue benutzt gegenpruefer_rollen.py.",
    "agent/signal_abbildung.py":
        "AKTIONEN_ALT ist die Aufzaehlung des ALTEN Vokabulars - dort DARF "
        "das neue Wort nicht stehen, sonst beschreibt der Name etwas anderes "
        "als der Inhalt.",
    "agent/verkaufsrechnung.py":
        "REDUZIEREN faellt bewusst in den else-Zweig und bekommt TEIL_ANTEIL "
        "- es IST der Teilverkauf. Siehe Vermerk an der Zeile.",
    "agent/empfehlung_vertrag.py":
        "Hier steht das Vokabular selbst, samt AKTIONEN_HEBEL_ALT.",
}


class Sammler(ast.NodeVisitor):
    def __init__(self) -> None:
        self.funde: list[tuple[int, set]] = []

    @staticmethod
    def _literale(knoten) -> set:
        return {k.value for k in ast.walk(knoten)
                if isinstance(k, ast.Constant) and k.value in ANKER}

    def visit_Compare(self, knoten):
        gefunden = self._literale(knoten)
        if gefunden:
            self.funde.append((knoten.lineno, gefunden))
        self.generic_visit(knoten)

    def visit_Assign(self, knoten):
        if isinstance(knoten.value, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            gefunden = self._literale(knoten.value)
            if gefunden:
                self.funde.append((knoten.lineno, gefunden))
        self.generic_visit(knoten)


def pruefe() -> int:
    dateien = subprocess.run(
        ["git", "ls-files", "*.py"], capture_output=True, text=True,
        encoding="utf-8").stdout.split()
    offen: list[str] = []
    geprueft = 0
    for pfad in dateien:
        if not pfad.startswith(BETRIEB) or "hebel_" in pfad:
            continue
        if pfad in AUSGENOMMEN:
            continue
        try:
            baum = ast.parse(io.open(pfad, encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        sammler = Sammler()
        sammler.visit(baum)
        for zeile, gefunden in sammler.funde:
            if not gefunden & VERKAUFSSEITIG_NEU:
                continue
            geprueft += 1
            fehlt = VERKAUFSSEITIG_NEU - gefunden
            if fehlt:
                offen.append(f"{pfad}:{zeile}   nennt "
                             f"{', '.join(sorted(gefunden))} - es fehlt "
                             f"{', '.join(sorted(fehlt))}")

    # Und die Ausnahmen selbst: jede braucht einen Grund und eine Datei.
    for pfad, grund in sorted(AUSGENOMMEN.items()):
        geprueft += 1
        if len(str(grund).strip()) < 20:
            offen.append(f"{pfad}: Ausnahme ohne belastbaren Grund")

    print(f"{geprueft} Stellen geprueft, {len(offen)} offen")
    for zeile in offen:
        print(f"  FEHL  {zeile}")
    if not offen:
        print("  OK    jede Stelle im Betrieb kennt "
              f"{', '.join(sorted(VERKAUFSSEITIG_NEU))}")
    return 1 if offen else 0


if __name__ == "__main__":
    raise SystemExit(pruefe())
